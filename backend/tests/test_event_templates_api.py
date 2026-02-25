"""Event Templates API 测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.event import ChecklistTemplateItem, EventTemplate
from app.models.user import User


def _create_template(
    db_session: Session,
    community_id: int,
    name: str = "测试模板",
    event_type: str = "online",
    is_public: bool = False,
    created_by_id: int | None = None,
) -> EventTemplate:
    t = EventTemplate(
        community_id=community_id,
        name=name,
        event_type=event_type,
        is_public=is_public,
        created_by_id=created_by_id,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


def _create_template_item(
    db_session: Session,
    template_id: int,
    phase: str = "pre",
    title: str = "准备工作",
    order: int = 1,
) -> ChecklistTemplateItem:
    item = ChecklistTemplateItem(
        template_id=template_id,
        phase=phase,
        title=title,
        order=order,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


class TestListEventTemplates:
    def test_list_empty(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_includes_public_templates(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """公开模板对所有用户可见"""
        _create_template(db_session, test_community.id, name="公开模板", is_public=True)
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "公开模板" in names

    def test_list_excludes_other_users_private_templates(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_another_community: Community,
    ):
        """其他用户的私有模板不在列表中"""
        _create_template(
            db_session,
            test_another_community.id,
            name="他人私有模板",
            is_public=False,
            created_by_id=9999,  # 不存在的用户 id
        )
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "他人私有模板" not in names

    def test_list_includes_own_private_templates(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """自己创建的私有模板也出现在列表中"""
        _create_template(
            db_session,
            test_community.id,
            name="我的私有模板",
            is_public=False,
            created_by_id=test_user.id,
        )
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "我的私有模板" in names

    def test_list_public_template_from_another_community(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_another_community: Community,
    ):
        """其他社区的公开模板对所有社区可见"""
        _create_template(db_session, test_another_community.id, name="他社区公开模板", is_public=True)
        resp = client.get("/api/event-templates", headers=auth_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "他社区公开模板" in names


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

    def test_create_template_with_sop_fields(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """创建模板时可以携带 SOP 字段"""
        payload = {
            "name": "SOP 模板",
            "event_type": "online",
            "checklist_items": [
                {
                    "phase": "pre",
                    "title": "通知嘉宾",
                    "order": 1,
                    "is_mandatory": True,
                    "responsible_role": "主办方",
                    "deadline_offset_days": -7,
                    "estimated_hours": 2.5,
                    "reference_url": "https://example.com/guide",
                    "description": "提前一周通知所有嘉宾",
                },
            ],
        }
        resp = client.post("/api/event-templates", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        item = data["checklist_items"][0]
        assert item["is_mandatory"] is True
        assert item["responsible_role"] == "主办方"
        assert item["deadline_offset_days"] == -7
        assert item["estimated_hours"] == 2.5
        assert item["reference_url"] == "https://example.com/guide"


class TestGetEventTemplate:
    def test_get_existing_public_template(
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

    def test_get_own_private_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """创建者可以访问自己的私有模板"""
        t = _create_template(
            db_session, test_community.id, is_public=False, created_by_id=test_user.id
        )
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

    def test_get_other_users_private_template_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_another_community: Community,
    ):
        """其他用户的私有模板无权访问"""
        t = _create_template(
            db_session,
            test_another_community.id,
            is_public=False,
            created_by_id=9999,
        )
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
    def test_update_own_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """创建者可以修改自己的模板"""
        t = _create_template(
            db_session, test_community.id, name="旧名称", created_by_id=test_user.id
        )
        resp = client.patch(
            f"/api/event-templates/{t.id}",
            json={"name": "新名称"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"

    def test_update_other_users_template_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """非创建者无权修改模板"""
        t = _create_template(
            db_session,
            test_community.id,
            name="他人模板",
            created_by_id=9999,
        )
        resp = client.patch(
            f"/api/event-templates/{t.id}",
            json={"name": "改名"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

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

    def test_superuser_can_update_any_template(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """超级管理员可以修改任意模板"""
        t = _create_template(
            db_session,
            test_community.id,
            name="原名称",
            created_by_id=9999,
        )
        resp = client.patch(
            f"/api/event-templates/{t.id}",
            json={"name": "超管改名"},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "超管改名"


class TestDeleteEventTemplate:
    def test_delete_own_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """创建者可以删除自己的模板"""
        t = _create_template(
            db_session, test_community.id, created_by_id=test_user.id
        )
        resp = client.delete(f"/api/event-templates/{t.id}", headers=auth_headers)
        assert resp.status_code == 204
        assert db_session.query(EventTemplate).filter(EventTemplate.id == t.id).first() is None

    def test_delete_other_users_template_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """非创建者无权删除模板"""
        t = _create_template(
            db_session, test_community.id, created_by_id=9999
        )
        resp = client.delete(f"/api/event-templates/{t.id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent_template(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        resp = client.delete("/api/event-templates/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_superuser_can_delete_any_template(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """超级管理员可以删除任意模板"""
        t = _create_template(
            db_session, test_community.id, created_by_id=9999
        )
        resp = client.delete(f"/api/event-templates/{t.id}", headers=superuser_auth_headers)
        assert resp.status_code == 204


class TestTemplateItemCRUD:
    def test_add_item_to_own_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """创建者可以向自己的模板添加条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=test_user.id
        )
        payload = {
            "phase": "pre",
            "title": "新条目",
            "order": 1,
            "is_mandatory": True,
            "responsible_role": "策划",
            "deadline_offset_days": -3,
            "estimated_hours": 1.0,
            "reference_url": "https://example.com",
            "description": "条目说明",
        }
        resp = client.post(
            f"/api/event-templates/{t.id}/items",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "新条目"
        assert data["is_mandatory"] is True
        assert data["responsible_role"] == "策划"
        assert data["deadline_offset_days"] == -3

    def test_add_item_to_other_users_template_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """非创建者无权向模板添加条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=9999
        )
        resp = client.post(
            f"/api/event-templates/{t.id}/items",
            json={"phase": "pre", "title": "强行添加", "order": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_add_item_nonexistent_template(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        resp = client.post(
            "/api/event-templates/99999/items",
            json={"phase": "pre", "title": "测试", "order": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_template_item(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """创建者可以修改模板条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=test_user.id
        )
        item = _create_template_item(db_session, t.id, title="旧标题")
        resp = client.patch(
            f"/api/event-templates/{t.id}/items/{item.id}",
            json={"title": "新标题", "responsible_role": "主持人"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "新标题"
        assert data["responsible_role"] == "主持人"

    def test_update_template_item_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """非创建者无权修改条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=9999
        )
        item = _create_template_item(db_session, t.id)
        resp = client.patch(
            f"/api/event-templates/{t.id}/items/{item.id}",
            json={"title": "强行修改"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_update_nonexistent_item(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """修改不存在条目返回 404"""
        t = _create_template(
            db_session, test_community.id, created_by_id=test_user.id
        )
        resp = client.patch(
            f"/api/event-templates/{t.id}/items/99999",
            json={"title": "不存在"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_template_item(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user: User,
    ):
        """创建者可以删除模板条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=test_user.id
        )
        item = _create_template_item(db_session, t.id)
        resp = client.delete(
            f"/api/event-templates/{t.id}/items/{item.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
        assert (
            db_session.query(ChecklistTemplateItem)
            .filter(ChecklistTemplateItem.id == item.id)
            .first()
        ) is None

    def test_delete_template_item_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """非创建者无权删除条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=9999
        )
        item = _create_template_item(db_session, t.id)
        resp = client.delete(
            f"/api/event-templates/{t.id}/items/{item.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_superuser_can_manage_any_template_items(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """超级管理员可以管理任意模板的条目"""
        t = _create_template(
            db_session, test_community.id, created_by_id=9999
        )
        resp = client.post(
            f"/api/event-templates/{t.id}/items",
            json={"phase": "during", "title": "超管添加", "order": 1},
            headers=superuser_auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "超管添加"
