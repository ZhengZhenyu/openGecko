"""
Tests for channel configuration API endpoints.

Endpoints tested:
- GET  /api/channels
- POST /api/channels
- PUT  /api/channels/{channel_id}
- DELETE /api/channels/{channel_id}

Permission model:
- list:   任何社区成员可查看（脱敏后）
- create: 仅平台超管
- update: 仅平台超管
- delete: 仅平台超管
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.channel import ChannelConfig
from app.models.community import Community
from app.models.user import User


# ─── helpers ──────────────────────────────────────────────────────────────────

def _create_channel(
    db_session: Session,
    community_id: int,
    channel: str = "wechat",
    config: dict | None = None,
    enabled: bool = True,
) -> ChannelConfig:
    cfg = ChannelConfig(
        channel=channel,
        community_id=community_id,
        config=config or {"app_id": "wx123", "app_secret": "sec_abc1234"},
        enabled=enabled,
    )
    db_session.add(cfg)
    db_session.commit()
    db_session.refresh(cfg)
    return cfg


# ─── GET /api/channels ────────────────────────────────────────────────────────

class TestListChannels:

    def test_list_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/channels", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_channels(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        _create_channel(db_session, test_community.id, "wechat")
        _create_channel(db_session, test_community.id, "hugo", config={"repo_path": "/tmp/blog"})

        response = client.get("/api/channels", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        channels_found = {item["channel"] for item in data}
        assert channels_found == {"wechat", "hugo"}

    def test_list_sensitive_fields_masked(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """敏感字段（app_secret）应脱敏，不应明文返回。"""
        _create_channel(
            db_session,
            test_community.id,
            "wechat",
            config={"app_id": "wx_public", "app_secret": "super_secret_key"},
        )

        response = client.get("/api/channels", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        cfg = data[0]
        # app_secret 应被脱敏，不能等于原始值
        assert cfg["config"]["app_secret"] != "super_secret_key"
        assert "••••" in cfg["config"]["app_secret"]
        # app_id 是非敏感字段，应正常显示
        assert cfg["config"]["app_id"] == "wx_public"

    def test_list_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """只返回当前社区的渠道配置，不能跨社区泄露。"""
        _create_channel(db_session, test_community.id, "wechat")
        _create_channel(db_session, test_another_community.id, "csdn")

        response = client.get("/api/channels", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["channel"] == "wechat"

    def test_list_no_auth(self, client: TestClient):
        response = client.get("/api/channels")
        assert response.status_code == 401


# ─── POST /api/channels ───────────────────────────────────────────────────────

class TestCreateChannel:

    def test_create_wechat_channel_success(
        self,
        client: TestClient,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        response = client.post(
            "/api/channels",
            json={
                "channel": "wechat",
                "config": {"app_id": "wxABC", "app_secret": "secret123"},
                "enabled": True,
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["channel"] == "wechat"
        assert data["enabled"] is True
        # app_id 不是敏感字段
        assert data["config"]["app_id"] == "wxABC"
        # app_secret 应脱敏
        assert "••••" in data["config"]["app_secret"]

    def test_create_hugo_channel_success(
        self,
        client: TestClient,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        response = client.post(
            "/api/channels",
            json={
                "channel": "hugo",
                "config": {"repo_path": "/var/www/blog", "content_dir": "content/posts"},
                "enabled": False,
            },
            headers=superuser_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["channel"] == "hugo"
        assert data["enabled"] is False

    def test_create_unsupported_channel(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
    ):
        response = client.post(
            "/api/channels",
            json={"channel": "unsupported_platform", "config": {}, "enabled": True},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 400

    def test_create_duplicate_channel(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        _create_channel(db_session, test_community.id, "wechat")

        response = client.post(
            "/api/channels",
            json={"channel": "wechat", "config": {}, "enabled": True},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 409

    def test_create_channel_requires_superuser(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """普通用户（即使是社区管理员）不能创建渠道。"""
        response = client.post(
            "/api/channels",
            json={"channel": "csdn", "config": {}, "enabled": False},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_channel_no_auth(self, client: TestClient):
        response = client.post(
            "/api/channels",
            json={"channel": "csdn", "config": {}, "enabled": False},
        )
        assert response.status_code == 401


# ─── PUT /api/channels/{channel_id} ──────────────────────────────────────────

class TestUpdateChannel:

    def test_update_channel_enabled(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        cfg = _create_channel(db_session, test_community.id, "hugo", enabled=False)

        response = client.put(
            f"/api/channels/{cfg.id}",
            json={"enabled": True},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is True

    def test_update_channel_config(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        cfg = _create_channel(
            db_session, test_community.id, "hugo",
            config={"repo_path": "/old/path"}
        )

        response = client.put(
            f"/api/channels/{cfg.id}",
            json={"config": {"repo_path": "/new/path"}},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["config"]["repo_path"] == "/new/path"

    def test_update_channel_not_found(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
    ):
        response = client.put(
            "/api/channels/99999",
            json={"enabled": True},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 404

    def test_update_channel_wrong_community(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        superuser_auth_headers: dict,
    ):
        """不能更新其他社区的渠道配置。"""
        cfg = _create_channel(db_session, test_another_community.id, "csdn")

        response = client.put(
            f"/api/channels/{cfg.id}",
            json={"enabled": True},
            headers=superuser_auth_headers,
        )
        assert response.status_code == 404

    def test_update_channel_requires_superuser(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        cfg = _create_channel(db_session, test_community.id, "csdn")
        response = client.put(
            f"/api/channels/{cfg.id}",
            json={"enabled": True},
            headers=auth_headers,
        )
        assert response.status_code == 403


# ─── DELETE /api/channels/{channel_id} ───────────────────────────────────────

class TestDeleteChannel:

    def test_delete_channel_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        cfg = _create_channel(db_session, test_community.id, "zhihu")

        response = client.delete(
            f"/api/channels/{cfg.id}", headers=superuser_auth_headers
        )
        assert response.status_code == 204

        # 验证已删除
        remaining = client.get("/api/channels", headers=superuser_auth_headers)
        assert remaining.json() == []

    def test_delete_channel_not_found(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
    ):
        response = client.delete("/api/channels/99999", headers=superuser_auth_headers)
        assert response.status_code == 404

    def test_delete_channel_wrong_community(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        superuser_auth_headers: dict,
    ):
        cfg = _create_channel(db_session, test_another_community.id, "wechat")
        response = client.delete(
            f"/api/channels/{cfg.id}", headers=superuser_auth_headers
        )
        assert response.status_code == 404

    def test_delete_channel_requires_superuser(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        cfg = _create_channel(db_session, test_community.id, "csdn")
        response = client.delete(f"/api/channels/{cfg.id}", headers=auth_headers)
        assert response.status_code == 403
