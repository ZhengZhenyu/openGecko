"""
Tests for RBAC (Role-Based Access Control) and content collaboration features.
"""

import pytest
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User, community_users
from app.models.community import Community
from app.models.content import Content
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def community_admin(db_session: Session, test_community: Community) -> User:
    """Create a community admin user."""
    user = User(
        username="communityadmin",
        email="communityadmin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Community Admin",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    
    # Add user to community with admin role
    stmt = insert(community_users).values(
        user_id=user.id,
        community_id=test_community.id,
        role='admin'
    )
    db_session.execute(stmt)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session, test_community: Community) -> User:
    """Create a regular user (non-admin)."""
    user = User(
        username="regularuser",
        email="regular@example.com",
        hashed_password=get_password_hash("pass123"),
        full_name="Regular User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    
    # Add user to community with user role
    stmt = insert(community_users).values(
        user_id=user.id,
        community_id=test_community.id,
        role='user'
    )
    db_session.execute(stmt)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(community_admin: User) -> str:
    """Generate JWT token for community admin."""
    return create_access_token(data={"sub": community_admin.username})


@pytest.fixture
def regular_user_token(regular_user: User) -> str:
    """Generate JWT token for regular user."""
    return create_access_token(data={"sub": regular_user.username})


@pytest.fixture
def test_content(db_session: Session, test_community: Community, regular_user: User) -> Content:
    """Create a test content owned by regular user."""
    content = Content(
        title="Test Content",
        content_markdown="# Test",
        content_html="<h1>Test</h1>",
        source_type="contribution",
        author="Test Author",
        status="draft",
        community_id=test_community.id,
        created_by_user_id=regular_user.id,
        owner_id=regular_user.id,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    return content


class TestRolePermissions:
    """Test role-based permissions."""
    
    def test_superuser_can_access_all_communities(
        self,
        client: TestClient,
        test_superuser: User,
        test_community: Community,
        test_another_community: Community,
        superuser_token: str
    ):
        """Superuser should be able to access all communities."""
        # Access first community
        headers = {
            "Authorization": f"Bearer {superuser_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.get("/api/contents", headers=headers)
        assert response.status_code == 200
        
        # Access another community
        headers["X-Community-Id"] = str(test_another_community.id)
        response = client.get("/api/contents", headers=headers)
        assert response.status_code == 200
    
    def test_regular_user_can_access_all_contents_cross_community(
        self,
        client: TestClient,
        regular_user: User,
        test_community: Community,
        test_another_community: Community,
        regular_user_token: str
    ):
        """内容采用 community association 模式，普通用户也可跨社区查看内容列表"""
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_another_community.id),
        }
        response = client.get("/api/contents", headers=headers)
        assert response.status_code == 200
    
    def test_community_admin_can_edit_all_community_content(
        self,
        client: TestClient,
        test_community: Community,
        community_admin: User,
        test_content: Content,
        admin_token: str
    ):
        """Community admin should be able to edit all content in their community."""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.put(
            f"/api/contents/{test_content.id}",
            headers=headers,
            json={"title": "Updated by Admin"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated by Admin"
    
    def test_regular_user_cannot_edit_others_content(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        regular_user_token: str
    ):
        """Regular user should not be able to edit content they don't own."""
        # Create content owned by admin
        admin_content = Content(
            title="Admin Content",
            content_markdown="# Admin",
            content_html="<h1>Admin</h1>",
            source_type="contribution",
            author="Admin",
            status="draft",
            community_id=test_community.id,
            created_by_user_id=community_admin.id,
            owner_id=community_admin.id,
        )
        db_session.add(admin_content)
        db_session.commit()
        db_session.refresh(admin_content)
        
        # Try to edit as regular user
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.put(
            f"/api/contents/{admin_content.id}",
            headers=headers,
            json={"title": "Hacked!"}
        )
        assert response.status_code == 403


class TestContentCollaboration:
    """Test content collaboration features."""
    
    def test_owner_can_add_collaborator(
        self,
        client: TestClient,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        test_content: Content,
        regular_user_token: str
    ):
        """Content owner should be able to add collaborators."""
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.post(
            f"/api/contents/{test_content.id}/collaborators/{community_admin.id}",
            headers=headers
        )
        assert response.status_code == 201
        assert response.json()["message"] == "Collaborator added successfully"
    
    def test_non_owner_cannot_add_collaborator(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        regular_user_token: str
    ):
        """Non-owner should not be able to add collaborators."""
        # Create content owned by admin
        admin_content = Content(
            title="Admin Content",
            content_markdown="# Admin",
            content_html="<h1>Admin</h1>",
            source_type="contribution",
            author="Admin",
            status="draft",
            community_id=test_community.id,
            created_by_user_id=community_admin.id,
            owner_id=community_admin.id,
        )
        db_session.add(admin_content)
        db_session.commit()
        db_session.refresh(admin_content)
        
        # Try to add collaborator as non-owner
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.post(
            f"/api/contents/{admin_content.id}/collaborators/{regular_user.id}",
            headers=headers
        )
        assert response.status_code == 403
    
    def test_collaborator_can_edit_content(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        test_content: Content,
        admin_token: str
    ):
        """Collaborator should be able to edit content."""
        # Add admin as collaborator
        test_content.collaborators.append(community_admin)
        db_session.commit()
        
        # Edit as collaborator
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.put(
            f"/api/contents/{test_content.id}",
            headers=headers,
            json={"title": "Edited by Collaborator"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Edited by Collaborator"
    
    def test_owner_can_remove_collaborator(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        test_content: Content,
        regular_user_token: str
    ):
        """Owner should be able to remove collaborators."""
        # Add admin as collaborator
        test_content.collaborators.append(community_admin)
        db_session.commit()
        
        # Remove collaborator
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.delete(
            f"/api/contents/{test_content.id}/collaborators/{community_admin.id}",
            headers=headers
        )
        assert response.status_code == 204
    
    def test_owner_can_transfer_ownership(
        self,
        client: TestClient,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        test_content: Content,
        regular_user_token: str
    ):
        """Owner should be able to transfer ownership."""
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.put(
            f"/api/contents/{test_content.id}/owner/{community_admin.id}",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["owner_id"] == community_admin.id
    
    def test_non_owner_cannot_transfer_ownership(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        regular_user_token: str
    ):
        """Non-owner (even as collaborator) should not be able to transfer ownership."""
        # Create content owned by community admin
        content = Content(
            title="Admin Content",
            content_markdown="# Admin",
            content_html="<h1>Admin</h1>",
            source_type="contribution",
            author="Admin",
            status="draft",
            community_id=test_community.id,
            created_by_user_id=community_admin.id,
            owner_id=community_admin.id,
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        # Add regular user as collaborator
        content.collaborators.append(regular_user)
        db_session.commit()
        
        # Try to transfer ownership as collaborator (not owner, not admin role)
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.put(
            f"/api/contents/{content.id}/owner/{regular_user.id}",
            headers=headers
        )
        # Should fail because collaborator is not owner
        assert response.status_code == 403


class TestCommunityRoleManagement:
    """Test community role management."""
    
    def test_superuser_can_update_user_role(
        self,
        client: TestClient,
        test_superuser: User,
        test_community: Community,
        regular_user: User,
        superuser_token: str
    ):
        """Superuser should be able to update user roles."""
        headers = {
            "Authorization": f"Bearer {superuser_token}",
        }
        response = client.put(
            f"/api/communities/{test_community.id}/users/{regular_user.id}/role?role=admin",
            headers=headers
        )
        assert response.status_code == 200
        assert "admin" in response.json()["message"]
    
    def test_regular_user_cannot_update_roles(
        self,
        client: TestClient,
        test_community: Community,
        regular_user: User,
        community_admin: User,
        regular_user_token: str
    ):
        """Regular user should not be able to update roles."""
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
        }
        response = client.put(
            f"/api/communities/{test_community.id}/users/{community_admin.id}/role?role=user",
            headers=headers
        )
        assert response.status_code == 403
    
    def test_invalid_role_rejected(
        self,
        client: TestClient,
        test_superuser: User,
        test_community: Community,
        regular_user: User,
        superuser_token: str
    ):
        """Invalid role should be rejected."""
        headers = {
            "Authorization": f"Bearer {superuser_token}",
        }
        response = client.put(
            f"/api/communities/{test_community.id}/users/{regular_user.id}/role?role=invalid",
            headers=headers
        )
        assert response.status_code == 400


class TestContentCreationWithOwnership:
    """Test content creation with ownership."""
    
    def test_content_creator_is_owner(
        self,
        client: TestClient,
        test_community: Community,
        regular_user: User,
        regular_user_token: str
    ):
        """When creating content, creator should be set as owner."""
        headers = {
            "Authorization": f"Bearer {regular_user_token}",
            "X-Community-Id": str(test_community.id),
        }
        response = client.post(
            "/api/contents",
            headers=headers,
            json={
                "title": "New Content",
                "content_markdown": "# New",
                "source_type": "contribution",
                "author": "Test"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["owner_id"] == regular_user.id
        assert data["created_by_user_id"] == regular_user.id
