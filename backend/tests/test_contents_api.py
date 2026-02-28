"""
Tests for content management API endpoints.

Endpoints tested:
- GET /api/contents
- POST /api/contents
- GET /api/contents/{content_id}
- PUT /api/contents/{content_id}
- DELETE /api/contents/{content_id}
- PATCH /api/contents/{content_id}/status
- PATCH /api/contents/{content_id}/schedule
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.community import Community
from app.models.content import Content


class TestListContents:
    """Tests for GET /api/contents"""

    def test_list_contents_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test listing contents in a community."""
        # Create test contents
        for i in range(3):
            content = Content(
                title=f"Test Content {i}",
                content_markdown=f"# Content {i}",
                content_html=f"<h1>Content {i}</h1>",
                author="Test Author",
                community_id=test_community.id,
                source_type="contribution",
            )
            db_session.add(content)
        db_session.commit()

        response = client.get("/api/contents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_contents_pagination(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test contents list pagination."""
        # Create 10 contents
        for i in range(10):
            content = Content(
                title=f"Content {i}",
                content_markdown="Test",
                content_html="<p>Test</p>",
                author="Author",
                community_id=test_community.id,
                source_type="contribution",
            )
            db_session.add(content)
        db_session.commit()

        # Test page 1
        response = client.get("/api/contents?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["total"] == 10

        # Test page 2
        response = client.get("/api/contents?page=2&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2

    def test_list_contents_filter_by_status(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test filtering contents by status."""
        # Create contents with different statuses
        for status in ["draft", "reviewing", "approved", "published"]:
            content = Content(
                title=f"{status.capitalize()} Content",
                content_markdown="Test",
                content_html="<p>Test</p>",
                author="Author",
                status=status,
                community_id=test_community.id,
                source_type="contribution",
            )
            db_session.add(content)
        db_session.commit()

        # Filter by draft
        response = client.get("/api/contents?status=draft", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "draft"

    def test_list_contents_filter_by_source_type(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test filtering contents by source_type."""
        # Create contents with different source types
        for source_type in ["contribution", "release_note", "event_summary"]:
            content = Content(
                title=f"{source_type} Content",
                content_markdown="Test",
                content_html="<p>Test</p>",
                author="Author",
                community_id=test_community.id,
                source_type=source_type,
            )
            db_session.add(content)
        db_session.commit()

        # Filter by release_note
        response = client.get(
            "/api/contents?source_type=release_note", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["source_type"] == "release_note"

    def test_list_contents_keyword_search(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test searching contents by keyword."""
        # Create contents with different titles
        content1 = Content(
            title="Python Tutorial",
            content_markdown="Learn Python",
            content_html="<p>Learn Python</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        content2 = Content(
            title="JavaScript Guide",
            content_markdown="Learn JS",
            content_html="<p>Learn JS</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add_all([content1, content2])
        db_session.commit()

        # Search for Python
        response = client.get("/api/contents?keyword=Python", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Python" in data["items"][0]["title"]

    def test_list_contents_cross_community(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """内容采用 community association 模式，所有社区内容均可见（跨社区列表）"""
        # Create content in test_community
        content1 = Content(
            title="My Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        # Create content in another_community
        content2 = Content(
            title="Other Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_another_community.id,
            source_type="contribution",
        )
        db_session.add_all([content1, content2])
        db_session.commit()

        # 跨社区：两个社区的内容均可见
        response = client.get("/api/contents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        titles = {item["title"] for item in data["items"]}
        assert "My Content" in titles
        assert "Other Content" in titles

    def test_list_contents_no_auth(self, client: TestClient):
        """Test listing contents fails without authentication."""
        response = client.get("/api/contents")
        assert response.status_code == 401


class TestCreateContent:
    """Tests for POST /api/contents"""

    def test_create_content_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a new content."""
        response = client.post(
            "/api/contents",
            headers=auth_headers,
            json={
                "title": "New Content",
                "content_markdown": "# Hello World\n\nThis is **markdown**.",
                "author": "Test Author",
                "tags": ["python", "tutorial"],
                "category": "programming",
                "source_type": "contribution",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Content"
        assert data["author"] == "Test Author"
        assert data["status"] == "draft"  # Default status
        assert data["source_type"] == "contribution"
        assert "Hello World" in data["content_html"]  # Markdown converted
        assert "tags" in data
        assert "category" in data

    def test_create_content_with_cover_image(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating content with cover image."""
        response = client.post(
            "/api/contents",
            headers=auth_headers,
            json={
                "title": "Content with Image",
                "content_markdown": "Test content",
                "author": "Author",
                "source_type": "contribution",
                "cover_image": "/uploads/test.jpg",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cover_image"] == "/uploads/test.jpg"

    def test_create_content_invalid_source_type(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating content with invalid source_type fails."""
        response = client.post(
            "/api/contents",
            headers=auth_headers,
            json={
                "title": "Invalid Source",
                "content_markdown": "Test",
                "author": "Author",
                "source_type": "invalid_type",  # Not in enum
            },
        )
        assert response.status_code in [400, 422]  # Validation error

    def test_create_content_no_auth(self, client: TestClient):
        """Test creating content fails without authentication."""
        response = client.post(
            "/api/contents",
            json={
                "title": "No Auth",
                "content_markdown": "Test",
                "author": "Author",
                "source_type": "contribution",
            },
        )
        assert response.status_code == 401


class TestGetContent:
    """Tests for GET /api/contents/{content_id}"""

    def test_get_content_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test getting content details."""
        content = Content(
            title="Test Content",
            content_markdown="# Test",
            content_html="<h1>Test</h1>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(f"/api/contents/{content.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Content"
        assert data["author"] == "Author"

    def test_get_content_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent content returns 404."""
        response = client.get("/api/contents/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_content_from_another_community(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """内容采用 community association 模式，可跨社区访问其他社区的内容"""
        content = Content(
            title="Other Content",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_another_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(f"/api/contents/{content.id}", headers=auth_headers)
        assert response.status_code == 200  # 跨社区内容可访问


class TestUpdateContent:
    """Tests for PUT /api/contents/{content_id}"""

    def test_update_content_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test updating content."""
        content = Content(
            title="Original Title",
            content_markdown="Original content",
            content_html="<p>Original</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.put(
            f"/api/contents/{content.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "content_markdown": "# Updated content",
                "author": "Updated Author",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert "Updated content" in data["content_html"]

    def test_update_content_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating non-existent content returns 404."""
        response = client.put(
            "/api/contents/99999",
            headers=auth_headers,
            json={"title": "Not Found"},
        )
        assert response.status_code == 404


class TestDeleteContent:
    """Tests for DELETE /api/contents/{content_id}"""

    def test_delete_content_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test deleting content."""
        content = Content(
            title="To Delete",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()
        content_id = content.id

        response = client.delete(f"/api/contents/{content_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify content is deleted
        deleted = db_session.get(Content, content_id)
        assert deleted is None

    def test_delete_content_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test deleting non-existent content returns 404."""
        response = client.delete("/api/contents/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateContentStatus:
    """Tests for PATCH /api/contents/{content_id}/status"""

    def test_update_status_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test updating content status."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            status="draft",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.patch(
            f"/api/contents/{content.id}/status",
            headers=auth_headers,
            json={"status": "reviewing"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewing"

    def test_update_status_invalid(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test updating to invalid status fails."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.patch(
            f"/api/contents/{content.id}/status",
            headers=auth_headers,
            json={"status": "invalid_status"},
        )
        assert response.status_code in [400, 422]  # Validation error

    def test_update_status_valid_transitions(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test all valid status transitions."""
        content = Content(
            title="Test",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            status="draft",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        # draft -> reviewing
        response = client.patch(
            f"/api/contents/{content.id}/status",
            headers=auth_headers,
            json={"status": "reviewing"},
        )
        assert response.status_code == 200

        # reviewing -> approved
        response = client.patch(
            f"/api/contents/{content.id}/status",
            headers=auth_headers,
            json={"status": "approved"},
        )
        assert response.status_code == 200

        # approved -> published
        response = client.patch(
            f"/api/contents/{content.id}/status",
            headers=auth_headers,
            json={"status": "published"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "published"


class TestContentSchedule:
    """Tests for PATCH /api/contents/{content_id}/schedule

    Covers the inline scheduling feature in ContentEdit.vue that allows
    users to set/clear a scheduled_publish_at directly from the editor,
    and syncs with the ContentCalendar FullCalendar view.
    """

    def _make_content(self, db_session: Session, community: Community, owner: User | None = None) -> Content:
        content = Content(
            title="Schedule Test Content",
            content_markdown="# Test",
            content_html="<h1>Test</h1>",
            author="Author",
            community_id=community.id,
            source_type="contribution",
        )
        if owner:
            content.owner_id = owner.id
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        return content

    def test_set_schedule_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """设置有效排期时间，返回 200 并包含 scheduled_publish_at。"""
        content = self._make_content(db_session, test_community, owner=test_user)
        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            headers=auth_headers,
            json={"scheduled_publish_at": "2026-06-01T10:00:00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content.id
        assert data["scheduled_publish_at"] is not None
        assert "2026-06-01" in data["scheduled_publish_at"]

    def test_clear_schedule_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """将排期设为 null 可以清除已有排期。"""
        from datetime import datetime
        content = self._make_content(db_session, test_community, owner=test_user)
        content.scheduled_publish_at = datetime(2026, 6, 1, 10, 0, 0)
        db_session.commit()

        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            headers=auth_headers,
            json={"scheduled_publish_at": None},
        )
        assert response.status_code == 200
        assert response.json()["scheduled_publish_at"] is None

    def test_schedule_reflected_in_get(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """排期设置后，GET /contents/{id} 返回一致的 scheduled_publish_at。"""
        content = self._make_content(db_session, test_community, owner=test_user)

        client.patch(
            f"/api/contents/{content.id}/schedule",
            headers=auth_headers,
            json={"scheduled_publish_at": "2026-09-15T09:30:00"},
        )

        get_resp = client.get(f"/api/contents/{content.id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert "2026-09-15" in (get_resp.json()["scheduled_publish_at"] or "")

    def test_schedule_not_found(
        self,
        client: TestClient,
        test_community: Community,
        auth_headers: dict,
    ):
        """内容不存在时返回 404。"""
        response = client.patch(
            "/api/contents/999999/schedule",
            headers=auth_headers,
            json={"scheduled_publish_at": "2026-06-01T10:00:00"},
        )
        assert response.status_code == 404

    def test_schedule_unauthenticated(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
    ):
        """未认证请求返回 401。"""
        content = self._make_content(db_session, test_community)
        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            headers={"X-Community-Id": str(test_community.id)},
            json={"scheduled_publish_at": "2026-06-01T10:00:00"},
        )
        assert response.status_code == 401

    def test_schedule_no_permission(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        test_another_community: Community,
        another_user_auth_headers: dict,
    ):
        """无权限用户（非所有者/协作者/管理员）返回 403。"""
        content = self._make_content(db_session, test_community, owner=test_user)
        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            headers=another_user_auth_headers,
            json={"scheduled_publish_at": "2026-06-01T10:00:00"},
        )
        assert response.status_code == 403

    def test_create_content_with_schedule(
        self,
        client: TestClient,
        test_community: Community,
        auth_headers: dict,
    ):
        """POST /contents 支持在创建时包含 scheduled_publish_at（ContentEdit 保存路径）。"""
        response = client.post(
            "/api/contents",
            headers=auth_headers,
            json={
                "title": "Scheduled New Content",
                "content_markdown": "# Hello",
                "content_html": "",
                "source_type": "contribution",
                "author": "Writer",
                "tags": [],
                "category": "",
                "work_status": "planning",
                "assignee_ids": [],
                "community_ids": [test_community.id],
                "scheduled_publish_at": "2026-07-20T08:00:00",
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["scheduled_publish_at"] is not None
        assert "2026-07-20" in data["scheduled_publish_at"]

    def test_update_content_with_schedule(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """PUT /contents/{id} 更新时同样可以修改 scheduled_publish_at（ContentEdit 保存路径）。"""
        content = self._make_content(db_session, test_community, owner=test_user)

        response = client.put(
            f"/api/contents/{content.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "content_markdown": "# Updated",
                "content_html": "",
                "source_type": "contribution",
                "author": "Writer",
                "tags": [],
                "category": "",
                "work_status": "in_progress",
                "assignee_ids": [],
                "community_ids": [test_community.id],
                "scheduled_publish_at": "2026-08-10T14:00:00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["scheduled_publish_at"] is not None
        assert "2026-08-10" in data["scheduled_publish_at"]

    def test_update_clears_schedule_when_null(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """PUT /contents/{id} 传 scheduled_publish_at=null 时清除排期。"""
        from datetime import datetime
        content = self._make_content(db_session, test_community, owner=test_user)
        content.scheduled_publish_at = datetime(2026, 8, 10, 14, 0, 0)
        db_session.commit()

        response = client.put(
            f"/api/contents/{content.id}",
            headers=auth_headers,
            json={
                "title": "Clear Schedule",
                "content_markdown": "# Test",
                "content_html": "",
                "source_type": "contribution",
                "author": "Writer",
                "tags": [],
                "category": "",
                "work_status": "planning",
                "assignee_ids": [],
                "community_ids": [test_community.id],
                "scheduled_publish_at": None,
            },
        )
        assert response.status_code == 200
        assert response.json()["scheduled_publish_at"] is None

    def test_schedule_superuser_can_schedule_any(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        superuser_auth_headers: dict,
    ):
        """超级管理员可以为任意内容设置排期。"""
        content = self._make_content(db_session, test_community, owner=test_user)
        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            headers=superuser_auth_headers,
            json={"scheduled_publish_at": "2026-12-31T23:59:00"},
        )
        assert response.status_code == 200
        assert "2026-12-31" in response.json()["scheduled_publish_at"]

