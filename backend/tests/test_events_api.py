"""Events API 测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.event import Event


def _create_event(
    db_session: Session,
    community_id: int,
    title: str = "测试活动",
    status: str = "draft",
    event_type: str = "offline",
) -> Event:
    event = Event(
        community_id=community_id,
        title=title,
        status=status,
        event_type=event_type,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


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

    def test_delete_cancelled_event(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_community: Community,
    ):
        """已取消状态的活动也可以被删除"""
        event = _create_event(
            db_session, test_community.id, title="已取消活动", status="cancelled"
        )
        resp = client.delete(f"/api/events/{event.id}", headers=auth_headers)
        assert resp.status_code == 204
