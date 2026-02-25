"""Events API 测试"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.event import ChecklistItem, Event, EventTemplate, ChecklistTemplateItem


def _create_event(
    db_session: Session,
    community_id: int,
    title: str = "测试活动",
    status: str = "planning",
    event_type: str = "offline",
    planned_at=None,
) -> Event:
    event = Event(
        community_id=community_id,
        title=title,
        status=status,
        event_type=event_type,
        planned_at=planned_at,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def _create_checklist_item(
    db_session: Session,
    event_id: int,
    title: str = "测试清单项",
    phase: str = "pre",
    status: str = "pending",
) -> ChecklistItem:
    item = ChecklistItem(
        event_id=event_id,
        title=title,
        phase=phase,
        status=status,
        order=1,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def _create_template_with_items(
    db_session: Session,
    community_id: int,
    created_by_id: int,
    planned_offset_days: int = -7,
) -> EventTemplate:
    template = EventTemplate(
        community_id=community_id,
        name="测试 SOP 模板",
        event_type="online",
        is_public=True,
        created_by_id=created_by_id,
    )
    db_session.add(template)
    db_session.flush()

    item = ChecklistTemplateItem(
        template_id=template.id,
        phase="pre",
        title="提前准备",
        order=1,
        deadline_offset_days=planned_offset_days,
        is_mandatory=True,
        responsible_role="策划",
        description="详细说明",
        reference_url="https://example.com",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(template)
    return template


class TestDeleteEvent:
    def test_delete_event_success(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """成功删除活动返回 204，数据库中不再存在该活动"""
        event = _create_event(db_session, test_community.id, title="待删除活动")
        event_id = event.id

        resp = client.delete(f"/api/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 204

        deleted = db_session.query(Event).filter(Event.id == event_id).first()
        assert deleted is None

    def test_delete_event_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """删除不存在的活动返回 404"""
        resp = client.delete("/api/events/999999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_event_no_auth(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
    ):
        """未登录删除活动返回 401"""
        event = _create_event(db_session, test_community.id, title="未认证删除测试")
        resp = client.delete(f"/api/events/{event.id}")
        assert resp.status_code == 401

    def test_delete_completed_event(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """已完成状态的活动也可以被删除"""
        event = _create_event(
            db_session, test_community.id, title="已完成活动", status="completed"
        )
        resp = client.delete(f"/api/events/{event.id}", headers=auth_headers)
        assert resp.status_code == 204


class TestChecklistCompletedAt:
    def test_done_status_sets_completed_at(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """将清单项状态改为 done 时，completed_at 自动设置"""
        event = _create_event(db_session, test_community.id)
        item = _create_checklist_item(db_session, event.id, status="pending")

        resp = client.patch(
            f"/api/events/{event.id}/checklist/{item.id}",
            json={"status": "done"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

    def test_done_status_does_not_overwrite_existing_completed_at(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """已有 completed_at 的条目再次标记 done 不覆盖原时间"""
        from datetime import datetime, timezone
        event = _create_event(db_session, test_community.id)
        fixed_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        item = ChecklistItem(
            event_id=event.id,
            title="已完成项",
            phase="pre",
            status="done",
            order=1,
            completed_at=fixed_time,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        resp = client.patch(
            f"/api/events/{event.id}/checklist/{item.id}",
            json={"status": "done"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # completed_at 不被覆盖，仍是原来的时间
        assert data["completed_at"] is not None
        assert "2025-01-01" in data["completed_at"]

    def test_pending_status_clears_completed_at(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """将已完成条目改回 pending 时，completed_at 被清除"""
        from datetime import datetime, timezone
        event = _create_event(db_session, test_community.id)
        item = ChecklistItem(
            event_id=event.id,
            title="待重置项",
            phase="pre",
            status="done",
            order=1,
            completed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        resp = client.patch(
            f"/api/events/{event.id}/checklist/{item.id}",
            json={"status": "pending"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["completed_at"] is None

    def test_skipped_status_clears_completed_at(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """将条目标为 skipped 时，completed_at 被清除"""
        from datetime import datetime, timezone
        event = _create_event(db_session, test_community.id)
        item = ChecklistItem(
            event_id=event.id,
            title="跳过项",
            phase="pre",
            status="done",
            order=1,
            completed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        resp = client.patch(
            f"/api/events/{event.id}/checklist/{item.id}",
            json={"status": "skipped"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["completed_at"] is None


class TestCreateEventFromTemplate:
    def test_create_event_copies_template_checklist(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user,
    ):
        """从模板创建活动时，清单条目被正确复制"""
        template = _create_template_with_items(
            db_session, test_community.id, test_user.id
        )

        payload = {
            "title": "模板测试活动",
            "event_type": "online",
            "community_id": test_community.id,
            "community_ids": [test_community.id],
            "template_id": template.id,
        }
        resp = client.post("/api/events", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]

        checklist_resp = client.get(
            f"/api/events/{event_id}/checklist", headers=auth_headers
        )
        assert checklist_resp.status_code == 200
        items = checklist_resp.json()
        assert len(items) == 1
        item = items[0]
        assert item["title"] == "提前准备"
        assert item["is_mandatory"] is True
        assert item["responsible_role"] == "策划"
        assert item["description"] == "详细说明"
        assert item["reference_url"] == "https://example.com"

    def test_create_event_computes_due_date_from_offset(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
        test_user,
    ):
        """deadline_offset_days 相对活动日期正确计算 due_date"""
        template = _create_template_with_items(
            db_session, test_community.id, test_user.id, planned_offset_days=-7
        )

        planned_date = date.today() + timedelta(days=30)
        payload = {
            "title": "有日期活动",
            "event_type": "online",
            "community_id": test_community.id,
            "community_ids": [test_community.id],
            "template_id": template.id,
            "planned_at": planned_date.isoformat(),
        }
        resp = client.post("/api/events", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]

        checklist_resp = client.get(
            f"/api/events/{event_id}/checklist", headers=auth_headers
        )
        items = checklist_resp.json()
        assert len(items) == 1
        expected_due = (planned_date + timedelta(days=-7)).isoformat()
        assert items[0]["due_date"] == expected_due

    def test_create_event_without_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """不指定模板时，活动清单为空"""
        payload = {
            "title": "无模板活动",
            "event_type": "offline",
            "community_id": test_community.id,
            "community_ids": [test_community.id],
        }
        resp = client.post("/api/events", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]

        checklist_resp = client.get(
            f"/api/events/{event_id}/checklist", headers=auth_headers
        )
        assert checklist_resp.json() == []

    def test_create_event_with_nonexistent_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """指定不存在的模板 ID 时，活动正常创建但清单为空"""
        payload = {
            "title": "无效模板活动",
            "event_type": "online",
            "community_id": test_community.id,
            "community_ids": [test_community.id],
            "template_id": 99999,
        }
        resp = client.post("/api/events", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]

        checklist_resp = client.get(
            f"/api/events/{event_id}/checklist", headers=auth_headers
        )
        assert checklist_resp.json() == []


class TestChecklistCRUD:
    """POST/PATCH/DELETE /events/{event_id}/checklist 端点测试"""

    # ── POST create ────────────────────────────────────────────────────────────

    def test_create_checklist_item_minimal(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """仅提供必填字段（phase + title）可成功创建清单项"""
        event = _create_event(db_session, test_community.id)
        resp = client.post(
            f"/api/events/{event.id}/checklist",
            json={"phase": "pre", "title": "最简清单项"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "最简清单项"
        assert data["phase"] == "pre"
        assert data["status"] == "pending"
        assert data["is_mandatory"] is False
        assert data["description"] is None

    def test_create_checklist_item_full(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """提供全部可选字段时，所有字段均被正确保存"""
        event = _create_event(db_session, test_community.id)
        payload = {
            "phase": "during",
            "title": "完整清单项",
            "description": "详细说明",
            "is_mandatory": True,
            "responsible_role": "主持人",
            "reference_url": "https://example.com",
            "due_date": "2025-12-01",
            "notes": "备注内容",
            "order": 5,
        }
        resp = client.post(
            f"/api/events/{event.id}/checklist",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["phase"] == "during"
        assert data["title"] == "完整清单项"
        assert data["description"] == "详细说明"
        assert data["is_mandatory"] is True
        assert data["responsible_role"] == "主持人"
        assert data["reference_url"] == "https://example.com"
        assert data["due_date"] == "2025-12-01"
        assert data["notes"] == "备注内容"
        assert data["order"] == 5

    def test_create_checklist_item_different_phases(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """可为三个阶段分别创建清单项"""
        event = _create_event(db_session, test_community.id)
        for phase in ("pre", "during", "post"):
            resp = client.post(
                f"/api/events/{event.id}/checklist",
                json={"phase": phase, "title": f"{phase} 清单项"},
                headers=auth_headers,
            )
            assert resp.status_code == 201
            assert resp.json()["phase"] == phase

        checklist_resp = client.get(
            f"/api/events/{event.id}/checklist", headers=auth_headers
        )
        assert len(checklist_resp.json()) == 3

    def test_create_checklist_item_event_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """活动不存在时返回 404"""
        resp = client.post(
            "/api/events/999999/checklist",
            json={"phase": "pre", "title": "项目"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_checklist_item_no_auth(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
    ):
        """未登录时返回 401"""
        event = _create_event(db_session, test_community.id)
        resp = client.post(
            f"/api/events/{event.id}/checklist",
            json={"phase": "pre", "title": "未认证项"},
        )
        assert resp.status_code == 401

    # ── PATCH update (extended fields) ────────────────────────────────────────

    def test_update_checklist_item_extended_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """PATCH 支持更新 title/description/phase/is_mandatory/responsible_role/reference_url"""
        event = _create_event(db_session, test_community.id)
        item = _create_checklist_item(db_session, event.id, title="原标题", phase="pre")

        resp = client.patch(
            f"/api/events/{event.id}/checklist/{item.id}",
            json={
                "title": "新标题",
                "description": "新说明",
                "phase": "post",
                "is_mandatory": True,
                "responsible_role": "后勤",
                "reference_url": "https://new.example.com",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "新标题"
        assert data["description"] == "新说明"
        assert data["phase"] == "post"
        assert data["is_mandatory"] is True
        assert data["responsible_role"] == "后勤"
        assert data["reference_url"] == "https://new.example.com"

    def test_update_checklist_item_partial(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """PATCH 只传部分字段时，其余字段不受影响"""
        event = _create_event(db_session, test_community.id)
        item = _create_checklist_item(db_session, event.id, title="保持不变", phase="pre")

        resp = client.patch(
            f"/api/events/{event.id}/checklist/{item.id}",
            json={"is_mandatory": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "保持不变"
        assert data["phase"] == "pre"
        assert data["is_mandatory"] is True

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_checklist_item_success(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """成功删除清单项，返回 204，数据库中不再存在"""
        event = _create_event(db_session, test_community.id)
        item = _create_checklist_item(db_session, event.id, title="待删除清单项")
        item_id = item.id

        resp = client.delete(
            f"/api/events/{event.id}/checklist/{item_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        deleted = db_session.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
        assert deleted is None

    def test_delete_checklist_item_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """删除不存在的清单项返回 404"""
        event = _create_event(db_session, test_community.id)
        resp = client.delete(
            f"/api/events/{event.id}/checklist/999999",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_checklist_item_wrong_event(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """用错误的 event_id 删除时返回 404（跨活动隔离）"""
        event1 = _create_event(db_session, test_community.id, title="活动1")
        event2 = _create_event(db_session, test_community.id, title="活动2")
        item = _create_checklist_item(db_session, event1.id)

        # 用 event2 的路径去删 event1 的条目
        resp = client.delete(
            f"/api/events/{event2.id}/checklist/{item.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

        # 原条目仍然存在
        still_exists = db_session.query(ChecklistItem).filter(ChecklistItem.id == item.id).first()
        assert still_exists is not None

    def test_delete_checklist_item_no_auth(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
    ):
        """未登录时返回 401"""
        event = _create_event(db_session, test_community.id)
        item = _create_checklist_item(db_session, event.id)
        resp = client.delete(f"/api/events/{event.id}/checklist/{item.id}")
        assert resp.status_code == 401
