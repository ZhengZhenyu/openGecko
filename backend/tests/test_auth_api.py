"""
Tests for authentication API endpoints.

Endpoints tested:
- POST /api/auth/login
- POST /api/auth/register
- GET /api/auth/me
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
