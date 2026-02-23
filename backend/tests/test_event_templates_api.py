"""Event Templates API 测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.event import EventTemplate
from app.models.user import User


def _create_template(
    db_session: Session,
    community_id: int,
    name: str = "测试模板",
    event_type: str = "online",
    is_public: bool = False,
) -> EventTemplate:
    t = EventTemplate(
        community_id=community_id,
        name=name,
        event_type=event_type,
        is_public=is_public,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


class TestListEventTemplates:
    def test_list_empty(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_public_templates_only(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """列表仅返回公开模板，私有模板不出现"""
        _create_template(db_session, test_community.id, name="私有模板", is_public=False)
        _create_template(db_session, test_community.id, name="公开模板", is_public=True)
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "公开模板" in names
        assert "私有模板" not in names

    def test_list_includes_public_templates(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_another_community: Community,
    ):
        """公开模板对所有社区可见"""
        _create_template(db_session, test_another_community.id, name="公开模板", is_public=True)
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "公开模板" in names


class TestCreateEventTemplate:
    def test_create_template_no_checklist(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        payload = {
            "name": "新活动模板",
            "event_type": "offline",
            "description": "线下活动模板",
            "is_public": False,
            "checklist_items": [],
        }
        resp = client.post("/api/event-templates", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新活动模板"
        assert data["event_type"] == "offline"
        assert data["checklist_items"] == []

    def test_create_template_with_checklist_items(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        payload = {
            "name": "带清单模板",
            "event_type": "hybrid",
            "checklist_items": [
                {"phase": "pre", "title": "准备会场", "order": 1},
                {"phase": "during", "title": "签到", "order": 2},
            ],
        }
        resp = client.post("/api/event-templates", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["checklist_items"]) == 2
        phases = {item["phase"] for item in data["checklist_items"]}
        assert "pre" in phases
        assert "during" in phases


class TestGetEventTemplate:
    def test_get_existing_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """GET 公开模板返回 200"""
        t = _create_template(db_session, test_community.id, is_public=True)
        resp = client.get(f"/api/event-templates/{t.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == t.id

    def test_get_public_template_from_other_community(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_another_community: Community,
    ):
        t = _create_template(db_session, test_another_community.id, is_public=True)
        resp = client.get(f"/api/event-templates/{t.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_private_template_from_other_community_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_another_community: Community,
    ):
        t = _create_template(db_session, test_another_community.id, is_public=False)
        resp = client.get(f"/api/event-templates/{t.id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_get_nonexistent_template(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        resp = client.get("/api/event-templates/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateEventTemplate:
    def test_update_template_name(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        t = _create_template(db_session, test_community.id, name="旧名称")
        resp = client.patch(
            f"/api/event-templates/{t.id}",
            json={"name": "新名称"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"

    def test_update_nonexistent_template(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        resp = client.patch(
            "/api/event-templates/99999",
            json={"name": "不存在"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
