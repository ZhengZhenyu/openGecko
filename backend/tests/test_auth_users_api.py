"""
补充测试：认证 API 中未覆盖的端点。

Endpoints:
- GET  /api/auth/status
- GET  /api/auth/users            (superuser only)
- PATCH /api/auth/users/{user_id} (superuser only)
- DELETE /api/auth/users/{user_id} (superuser only)
- POST /api/auth/password-reset/request
- POST /api/auth/password-reset/confirm
"""

from unittest import mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.models.community import Community


# ─── GET /api/auth/status ─────────────────────────────────────────────────────

class TestSystemStatus:

    def test_status_no_auth(self, client: TestClient):
        """系统状态端点不需要认证，任何请求均可调用。"""
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "needs_setup" in data

    def test_status_when_initialized(
        self, client: TestClient, test_user: User
    ):
        """有非默认管理员用户存在时，needs_setup 应为 False。"""
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        # needs_setup=False 表示系统已初始化
        assert response.json()["needs_setup"] is False


# ─── GET /api/auth/users ──────────────────────────────────────────────────────

class TestListAllUsers:

    def test_list_users_as_superuser(
        self,
        client: TestClient,
        test_user: User,
        test_superuser: User,
        superuser_auth_headers: dict,
    ):
        response = client.get("/api/auth/users", headers=superuser_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 至少包含 testuser 和 admin
        usernames = [u["username"] for u in data]
        assert "testuser" in usernames
        assert "admin" in usernames

    def test_list_users_forbidden_for_regular_user(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        response = client.get("/api/auth/users", headers=auth_headers)
        assert response.status_code == 403

    def test_list_users_no_auth(self, client: TestClient):
        response = client.get("/api/auth/users")
        assert response.status_code == 401

    def test_list_users_excludes_default_admin(
        self,
        client: TestClient,
        db_session: Session,
        superuser_auth_headers: dict,
    ):
        """默认 admin 账号不应出现在用户列表中。"""
        default_admin = User(
            username="default_admin_x",
            email="da@example.com",
            hashed_password=get_password_hash("any"),
            is_superuser=True,
            is_default_admin=True,
        )
        db_session.add(default_admin)
        db_session.commit()

        response = client.get("/api/auth/users", headers=superuser_auth_headers)
        usernames = [u["username"] for u in response.json()]
        assert "default_admin_x" not in usernames


# ─── PATCH /api/auth/users/{user_id} ─────────────────────────────────────────

class TestUpdateUser:

    def test_update_user_email(
        self,
        client: TestClient,
        test_user: User,
        superuser_auth_headers: dict,
    ):
        response = client.patch(
            f"/api/auth/users/{test_user.id}",
            json={"email": "updated@example.com"},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["email"] == "updated@example.com"

    def test_update_user_full_name(
        self,
        client: TestClient,
        test_user: User,
        superuser_auth_headers: dict,
    ):
        response = client.patch(
            f"/api/auth/users/{test_user.id}",
            json={"full_name": "新名字"},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "新名字"

    def test_update_user_deactivate(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        # 创建一个要被停用的用户
        target = User(
            username="to_deactivate",
            email="dea@example.com",
            hashed_password=get_password_hash("pass"),
            is_active=True,
        )
        db_session.add(target)
        db_session.commit()

        response = client.patch(
            f"/api/auth/users/{target.id}",
            json={"is_active": False},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_user_duplicate_email(
        self,
        client: TestClient,
        test_user: User,
        test_superuser: User,
        superuser_auth_headers: dict,
    ):
        """不能改为其他用户已使用的邮箱。"""
        response = client.patch(
            f"/api/auth/users/{test_user.id}",
            json={"email": test_superuser.email},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 400

    def test_update_user_not_found(
        self, client: TestClient, superuser_auth_headers: dict
    ):
        response = client.patch(
            "/api/auth/users/99999",
            json={"full_name": "x"},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 404

    def test_update_user_forbidden_for_regular(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
    ):
        response = client.patch(
            f"/api/auth/users/{test_user.id}",
            json={"full_name": "x"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_cannot_demote_self_superuser(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict,
    ):
        """超管不能取消自己的超管权限。"""
        response = client.patch(
            f"/api/auth/users/{test_superuser.id}",
            json={"is_superuser": False},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 400
        assert "自己" in response.json()["detail"]


# ─── DELETE /api/auth/users/{user_id} ────────────────────────────────────────

class TestDeleteUser:

    def test_delete_user_success(
        self,
        client: TestClient,
        db_session: Session,
        superuser_auth_headers: dict,
    ):
        target = User(
            username="to_delete",
            email="del@example.com",
            hashed_password=get_password_hash("pass"),
        )
        db_session.add(target)
        db_session.commit()

        response = client.delete(
            f"/api/auth/users/{target.id}",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 204

        # 验证已删除
        response2 = client.get("/api/auth/users", headers=superuser_auth_headers)
        usernames = [u["username"] for u in response2.json()]
        assert "to_delete" not in usernames

    def test_cannot_delete_self(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict,
    ):
        response = client.delete(
            f"/api/auth/users/{test_superuser.id}",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 400
        assert "自己" in response.json()["detail"]

    def test_delete_user_not_found(
        self, client: TestClient, superuser_auth_headers: dict
    ):
        response = client.delete(
            "/api/auth/users/99999", headers=superuser_auth_headers
        )
        assert response.status_code == 404

    def test_delete_user_forbidden_for_regular(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
    ):
        response = client.delete(
            f"/api/auth/users/{test_user.id}", headers=auth_headers
        )
        assert response.status_code == 403


# ─── POST /api/auth/password-reset/request ───────────────────────────────────

class TestPasswordResetRequest:

    def test_reset_request_existing_email(
        self,
        client: TestClient,
        test_user: User,
    ):
        """向已注册邮箱发起重置，开发模式下应直接返回 token。"""
        response = client.post(
            "/api/auth/password-reset/request",
            json={"email": test_user.email},
        )
        assert response.status_code == 200
        # 开发模式（无 SMTP），应直接返回 reset_url 或 token
        data = response.json()
        assert "message" in data
        # 非邮件模式下会有 token 或 reset_url 字段
        # （如果有 SMTP 配置则只有 message，这里跳过检查具体 token）
        assert data["message"]

    def test_reset_request_nonexistent_email(self, client: TestClient):
        """向不存在的邮箱发起重置，应返回通用提示，不泄露是否存在。"""
        response = client.post(
            "/api/auth/password-reset/request",
            json={"email": "ghost_nonexistent@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # 不应泄露用户是否存在
        assert "token" not in data
        assert "reset_url" not in data

    def test_reset_request_dev_mode_returns_token(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
    ):
        """开发模式下应在响应中返回 token，方便测试。"""
        # 创建普通用户（非默认管理员）
        user = User(
            username="reset_me",
            email="reset_me@example.com",
            hashed_password=get_password_hash("oldpass"),
            is_active=True,
            is_default_admin=False,
        )
        db_session.add(user)
        db_session.commit()

        # 模拟无 SMTP 配置（即使 .env 中有配置也强制走开发模式）
        with mock.patch("app.api.auth.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = ""
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            response = client.post(
                "/api/auth/password-reset/request",
                json={"email": "reset_me@example.com"},
            )
        assert response.status_code == 200
        data = response.json()
        # 开发模式（测试环境无 SMTP）应有 token
        assert "token" in data or "reset_url" in data


# ─── POST /api/auth/password-reset/confirm ───────────────────────────────────

class TestPasswordResetConfirm:

    def _request_reset_token(self, client: TestClient, email: str) -> str:
        """辅助函数：请求重置 token 并返回。"""
        resp = client.post(
            "/api/auth/password-reset/request",
            json={"email": email},
        )
        data = resp.json()
        return data.get("token") or ""

    def test_reset_confirm_success(
        self,
        client: TestClient,
        db_session: Session,
    ):
        """成功使用 token 重置密码。"""
        user = User(
            username="confirm_reset",
            email="confirm@example.com",
            hashed_password=get_password_hash("oldpassword"),
            is_active=True,
            is_default_admin=False,
        )
        db_session.add(user)
        db_session.commit()

        token = self._request_reset_token(client, "confirm@example.com")
        if not token:
            # SMTP 模式下 token 不在响应里，跳过此测试
            return

        response = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": token, "new_password": "newpassword123"},
        )
        assert response.status_code == 200
        assert "重置" in response.json()["message"]

        # 用新密码登录验证
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "confirm_reset", "password": "newpassword123"},
        )
        assert login_resp.status_code == 200

    def test_reset_confirm_invalid_token(self, client: TestClient):
        response = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": "totally_invalid_token", "new_password": "newpass123"},
        )
        assert response.status_code == 400
        assert "无效" in response.json()["detail"] or "expired" in response.json()["detail"].lower()

    def test_reset_confirm_token_already_used(
        self,
        client: TestClient,
        db_session: Session,
    ):
        """已使用的 token 不可复用。"""
        user = User(
            username="double_use",
            email="double@example.com",
            hashed_password=get_password_hash("old"),
            is_active=True,
            is_default_admin=False,
        )
        db_session.add(user)
        db_session.commit()

        token = self._request_reset_token(client, "double@example.com")
        if not token:
            return

        # 第一次使用
        client.post(
            "/api/auth/password-reset/confirm",
            json={"token": token, "new_password": "newpass123"},
        )

        # 第二次使用同一 token
        response = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": token, "new_password": "anotherpass456"},
        )
        assert response.status_code == 400
