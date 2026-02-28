"""
Tests for Admin API — Audit Log Query endpoint.
"""
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User
from app.models.community import Community


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _create_audit_log(
    db: Session,
    user: User,
    community: Community,
    action: str = "create_content",
    resource_type: str = "content",
    resource_id: int | None = 1,
    details: dict | None = None,
    ip_address: str | None = "127.0.0.1",
    created_at: datetime | None = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user.id,
        community_id=community.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    if created_at:
        log.created_at = created_at
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ─── TestAuditLogList ─────────────────────────────────────────────────────────

class TestAuditLogList:
    """Tests for GET /api/admin/audit-logs."""

    def test_superuser_can_list_logs(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        _create_audit_log(db_session, test_superuser, test_community, action="create_content")
        resp = client.get("/api/admin/audit-logs", headers=superuser_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 1
        item = body["items"][0]
        assert item["action"] == "create_content"
        assert item["username"] == test_superuser.username

    def test_admin_user_can_list_logs(
        self,
        client: TestClient,
        db_session: Session,
        test_user: User,
        auth_headers: dict,
        test_community: Community,
    ):
        """Community admin can access audit logs."""
        _create_audit_log(db_session, test_user, test_community, action="update_status")
        resp = client.get("/api/admin/audit-logs", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_unauthenticated_is_rejected(self, client: TestClient):
        resp = client.get("/api/admin/audit-logs")
        assert resp.status_code == 401

    def test_filter_by_action(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        _create_audit_log(db_session, test_superuser, test_community, action="publish_wechat")
        _create_audit_log(db_session, test_superuser, test_community, action="delete_content")
        resp = client.get(
            "/api/admin/audit-logs",
            params={"action": "publish"},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all("publish" in i["action"] for i in items)

    def test_filter_by_resource_type(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        _create_audit_log(db_session, test_superuser, test_community, resource_type="content")
        _create_audit_log(db_session, test_superuser, test_community, resource_type="channel")
        resp = client.get(
            "/api/admin/audit-logs",
            params={"resource_type": "content"},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["resource_type"] == "content" for i in items)

    def test_filter_by_community_id(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
        test_another_community: Community,
    ):
        _create_audit_log(db_session, test_superuser, test_community, action="action_a")
        _create_audit_log(db_session, test_superuser, test_another_community, action="action_b")
        resp = client.get(
            "/api/admin/audit-logs",
            params={"community_id": test_community.id},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["community_id"] == test_community.id for i in items)

    def test_filter_by_username(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        test_user: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        _create_audit_log(db_session, test_superuser, test_community, action="superuser_action")
        _create_audit_log(db_session, test_user, test_community, action="user_action")
        resp = client.get(
            "/api/admin/audit-logs",
            params={"username": test_superuser.username},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["username"] == test_superuser.username for i in items)

    def test_filter_by_date_range(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        now = datetime.now(timezone.utc)
        old = _create_audit_log(db_session, test_superuser, test_community, action="old_action")
        old.created_at = now - timedelta(days=10)
        db_session.commit()

        new_log = _create_audit_log(db_session, test_superuser, test_community, action="new_action")
        new_log.created_at = now - timedelta(days=1)
        db_session.commit()

        resp = client.get(
            "/api/admin/audit-logs",
            params={
                "from_date": (now - timedelta(days=3)).isoformat(),
                "to_date": now.isoformat(),
            },
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        actions = [i["action"] for i in items]
        assert "new_action" in actions
        assert "old_action" not in actions

    def test_pagination(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        for i in range(5):
            _create_audit_log(
                db_session, test_superuser, test_community,
                action=f"paginate_action_{i}",
            )
        resp = client.get(
            "/api/admin/audit-logs",
            params={"page": 1, "page_size": 2},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 2
        assert body["total"] >= 5
        assert body["page"] == 1
        assert body["page_size"] == 2

    def test_response_fields(
        self,
        client: TestClient,
        db_session: Session,
        test_superuser: User,
        superuser_auth_headers: dict,
        test_community: Community,
    ):
        _create_audit_log(
            db_session, test_superuser, test_community,
            action="field_test",
            resource_type="content",
            resource_id=42,
            details={"title": "Test"},
            ip_address="10.0.0.1",
        )
        resp = client.get("/api/admin/audit-logs", headers=superuser_auth_headers)
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        required_keys = {
            "id", "username", "full_name", "action",
            "resource_type", "resource_id", "community_id",
            "details", "ip_address", "created_at",
        }
        assert required_keys.issubset(set(item.keys()))

    def test_empty_result(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
    ):
        """When no logs match filters, should return empty list with total=0."""
        resp = client.get(
            "/api/admin/audit-logs",
            params={"action": "nonexistent_xyzzy_abc"},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_publish_trend_endpoint(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers: dict,
    ):
        """GET /api/analytics/trend/daily should return trend data."""
        resp = client.get("/api/analytics/trend/daily", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "days" in body
        assert body["days"] == 30
        # Each item must have date and count
        if body["items"]:
            assert "date" in body["items"][0]
            assert "count" in body["items"][0]

    def test_publish_trend_custom_days(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """GET /api/analytics/trend/daily?days=7 should return 7 days of data."""
        resp = client.get(
            "/api/analytics/trend/daily",
            params={"days": 7},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["days"] == 7
        assert len(body["items"]) == 7
