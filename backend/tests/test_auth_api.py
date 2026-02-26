"""
Tests for authentication API endpoints.

Endpoints tested:
- POST /api/auth/login
- POST /api/auth/register
- GET /api/auth/me
- PATCH /api/auth/me
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.community import Community


class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login with correct credentials."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login fails with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login fails with non-existent username."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "anypassword"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_inactive_user(
        self, client: TestClient, db_session: Session, test_community: Community
    ):
        """Test login fails for inactive user."""
        # Create inactive user
        from app.core.security import get_password_hash

        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=False,
            is_superuser=False,
        )
        inactive_user.communities.append(test_community)
        db_session.add(inactive_user)
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "inactive", "password": "pass123"},
        )
        assert response.status_code == 403
        assert "用户已被禁用" in response.json()["detail"]


class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_success(
        self, client: TestClient, test_community: Community, superuser_auth_headers: dict
    ):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "full_name": "New User",
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "hashed_password" not in data  # Should not expose password hash

    def test_register_duplicate_username(
        self, client: TestClient, test_user: User, superuser_auth_headers: dict
    ):
        """Test registration fails with duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "pass123",
                "full_name": "Different User",
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(
        self, client: TestClient, test_user: User, superuser_auth_headers: dict
    ):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": "testuser@example.com",  # Already exists
                "password": "pass123",
                "full_name": "Different User",
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient, superuser_auth_headers: dict):
        """Test registration fails with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "pass123",
                "full_name": "New User",
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client: TestClient, superuser_auth_headers: dict):
        """Test registration validates password length."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "123",  # Too short
                "full_name": "New User",
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 422  # Validation error


class TestGetCurrentUser:
    """Tests for GET /api/auth/me"""

    def test_get_me_success(
        self,
        client: TestClient,
        test_user: User,
        test_community: Community,
        user_token: str,
    ):
        """Test getting current user info with valid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "testuser@example.com"
        assert len(data["communities"]) == 1
        assert data["communities"][0]["name"] == "Test Community"

    def test_get_me_no_token(self, client: TestClient):
        """Test getting current user fails without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_get_me_invalid_token(self, client: TestClient):
        """Test getting current user fails with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_get_me_superuser(
        self,
        client: TestClient,
        test_superuser: User,
        test_community: Community,
        superuser_token: str,
    ):
        """Test getting current user info for superuser."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "admin"
        assert data["user"]["is_superuser"] is True

    def test_get_me_multiple_communities(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_community: Community,
        test_another_community: Community,
        user_token: str,
    ):
        """Test user with multiple communities."""
        # Add user to another community
        test_user.communities.append(test_another_community)
        db_session.commit()

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["communities"]) == 2
        community_names = [c["name"] for c in data["communities"]]
        assert "Test Community" in community_names
        assert "Another Community" in community_names


class TestUpdateMyProfile:
    """Tests for PATCH /api/auth/me - 用户自助修改个人资料"""

    def test_update_full_name(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """普通用户可以修改自己的 full_name。"""
        response = client.patch(
            "/api/auth/me",
            json={"full_name": "Updated Name"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["username"] == "testuser"  # 用户名不变

    def test_update_email(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """普通用户可以修改自己的邮箱。"""
        response = client.patch(
            "/api/auth/me",
            json={"email": "newemail@example.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_password_success(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """提供正确的当前密码后可以成功修改密码。"""
        response = client.patch(
            "/api/auth/me",
            json={
                "current_password": "testpass123",
                "new_password": "newsecurepass!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        # 修改后能用新密码登录
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "newsecurepass!"},
        )
        assert login_resp.status_code == 200

    def test_update_password_wrong_current_password(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """当前密码错误时拒绝修改密码。"""
        response = client.patch(
            "/api/auth/me",
            json={
                "current_password": "wrongpassword",
                "new_password": "newsecurepass!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400
        assert "当前密码不正确" in response.json()["detail"]

    def test_update_password_missing_current_password(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """没有提供 current_password 时拒绝修改密码。"""
        response = client.patch(
            "/api/auth/me",
            json={"new_password": "newsecurepass!"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400
        assert "修改密码时必须提供当前密码" in response.json()["detail"]

    def test_update_email_duplicate(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        test_superuser: User,
        user_token: str,
    ):
        """邮箱已被其他用户使用时拒绝修改。"""
        response = client.patch(
            "/api/auth/me",
            json={"email": "admin@example.com"},  # test_superuser 的邮箱
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400
        assert "该邮箱已被其他用户使用" in response.json()["detail"]

    def test_update_email_same_value(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """修改邮箱为当前已有邮箱时应成功（不触发唯一性冲突）。"""
        response = client.patch(
            "/api/auth/me",
            json={"email": "testuser@example.com"},  # 同一邮箱
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "testuser@example.com"

    def test_update_invalid_email_format(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """非法邮箱格式应被 Pydantic 拒绝（422）。"""
        response = client.patch(
            "/api/auth/me",
            json={"email": "not-an-email"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422

    def test_update_new_password_too_short(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """新密码过短应被 Pydantic 拒绝（422）。"""
        response = client.patch(
            "/api/auth/me",
            json={"current_password": "testpass123", "new_password": "123"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422

    def test_update_profile_unauthenticated(self, client: TestClient):
        """未认证请求应被拒绝（401）。"""
        response = client.patch(
            "/api/auth/me",
            json={"full_name": "Should Fail"},
        )
        assert response.status_code == 401

    def test_cannot_escalate_privilege(
        self, client: TestClient, test_user: User, user_token: str
    ):
        """PATCH /me 不接受 is_superuser 字段，不能自行提权。"""
        response = client.patch(
            "/api/auth/me",
            json={"full_name": "Hacker", "is_superuser": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # 字段会被忽略，但请求本身成功（Pydantic 过滤 extra fields）
        assert response.status_code == 200
        data = response.json()
        assert data["is_superuser"] is False  # 权限未被提升
