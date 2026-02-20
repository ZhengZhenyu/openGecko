"""
Tests for meetings API endpoints.

Endpoints tested:
- GET    /api/meetings
- POST   /api/meetings
- GET    /api/meetings/{id}
- PUT    /api/meetings/{id}
- DELETE /api/meetings/{id}
- POST   /api/meetings/{id}/reminders
- GET    /api/meetings/{id}/reminders
- GET    /api/meetings/{id}/participants
- POST   /api/meetings/{id}/participants
- DELETE /api/meetings/{id}/participants/{pid}
- GET    /api/meetings/{id}/minutes
- PUT    /api/meetings/{id}/minutes
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.committee import Committee, CommitteeMember
from app.models.meeting import Meeting, MeetingParticipant
from app.models.user import User, community_users


# ─── helpers ──────────────────────────────────────────────────────────────────

def _create_committee(db_session: Session, community_id: int, **kwargs) -> Committee:
    defaults = {"name": "技术委员会", "slug": "tech", "is_active": True}
    defaults.update(kwargs)
    c = Committee(community_id=community_id, **defaults)
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _create_meeting(
    db_session: Session,
    community_id: int,
    committee_id: int,
    title: str = "测试会议",
    **kwargs,
) -> Meeting:
    defaults = {
        "scheduled_at": datetime.utcnow() + timedelta(days=3),
        "duration": 60,
        "status": "scheduled",
        "work_status": "planning",
        "reminder_sent": False,
    }
    defaults.update(kwargs)
    m = Meeting(
        community_id=community_id,
        committee_id=committee_id,
        title=title,
        **defaults,
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


def _future_dt(days: int = 3) -> str:
    return (datetime.utcnow() + timedelta(days=days)).isoformat()


# ─── GET /api/meetings ────────────────────────────────────────────────────────

class TestListMeetings:

    def test_list_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/meetings", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_data(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        _create_meeting(db_session, test_community.id, committee.id, "会议 A")
        _create_meeting(db_session, test_community.id, committee.id, "会议 B")

        response = client.get("/api/meetings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = {m["title"] for m in data}
        assert "会议 A" in titles
        assert "会议 B" in titles

    def test_list_filter_by_committee(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        c1 = _create_committee(db_session, test_community.id, name="委员会1", slug="c1")
        c2 = _create_committee(db_session, test_community.id, name="委员会2", slug="c2")
        _create_meeting(db_session, test_community.id, c1.id, "C1 会议")
        _create_meeting(db_session, test_community.id, c2.id, "C2 会议")

        response = client.get(
            f"/api/meetings?committee_id={c1.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "C1 会议"

    def test_list_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        c1 = _create_committee(db_session, test_community.id, slug="c1")
        c2 = _create_committee(db_session, test_another_community.id, slug="c2")
        _create_meeting(db_session, test_community.id, c1.id, "我的会议")
        _create_meeting(db_session, test_another_community.id, c2.id, "隔壁社区会议")

        response = client.get("/api/meetings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "我的会议"

    def test_list_no_auth(self, client: TestClient):
        response = client.get("/api/meetings")
        assert response.status_code == 401


# ─── POST /api/meetings ───────────────────────────────────────────────────────

class TestCreateMeeting:

    def test_create_meeting_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)

        response = client.post(
            "/api/meetings",
            json={
                "committee_id": committee.id,
                "title": "新会议",
                "description": "会议描述",
                "scheduled_at": _future_dt(5),
                "duration": 90,
                "location_type": "online",
                "location": "Zoom",
                "agenda": "1. 议题一\n2. 议题二",
                "reminder_before_hours": 24,
                "assignee_ids": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "新会议"
        assert data["duration"] == 90
        assert data["status"] == "scheduled"
        assert "assignee_ids" in data

    def test_create_meeting_wrong_committee(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """不能使用其他社区的委员会创建会议。"""
        other_committee = _create_committee(db_session, test_another_community.id, slug="other")

        response = client.post(
            "/api/meetings",
            json={
                "committee_id": other_committee.id,
                "title": "越权会议",
                "scheduled_at": _future_dt(),
                "duration": 60,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_meeting_no_auth(self, client: TestClient):
        response = client.post(
            "/api/meetings",
            json={"committee_id": 1, "title": "xxx", "scheduled_at": _future_dt()},
        )
        assert response.status_code == 401


# ─── GET /api/meetings/{id} ───────────────────────────────────────────────────

class TestGetMeeting:

    def test_get_meeting_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id, "获取测试")

        response = client.get(f"/api/meetings/{meeting.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meeting.id
        assert data["title"] == "获取测试"

    def test_get_meeting_not_found(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/meetings/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_meeting_wrong_community(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        auth_headers: dict,
    ):
        c = _create_committee(db_session, test_another_community.id, slug="x")
        meeting = _create_meeting(db_session, test_another_community.id, c.id)

        response = client.get(f"/api/meetings/{meeting.id}", headers=auth_headers)
        assert response.status_code == 404


# ─── PUT /api/meetings/{id} ───────────────────────────────────────────────────

class TestUpdateMeeting:

    def test_update_meeting_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id, "原标题")

        response = client.put(
            f"/api/meetings/{meeting.id}",
            json={"title": "新标题", "status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"
        assert data["status"] == "completed"

    def test_update_meeting_not_found(self, client: TestClient, auth_headers: dict):
        response = client.put(
            "/api/meetings/99999",
            json={"title": "x"},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ─── DELETE /api/meetings/{id} ────────────────────────────────────────────────

class TestDeleteMeeting:

    def test_delete_meeting_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.delete(f"/api/meetings/{meeting.id}", headers=auth_headers)
        assert response.status_code == 204

        get_resp = client.get(f"/api/meetings/{meeting.id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_meeting_not_found(self, client: TestClient, auth_headers: dict):
        response = client.delete("/api/meetings/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_meeting_wrong_community(
        self,
        client: TestClient,
        db_session: Session,
        test_another_community: Community,
        auth_headers: dict,
    ):
        c = _create_committee(db_session, test_another_community.id, slug="y")
        meeting = _create_meeting(db_session, test_another_community.id, c.id)

        response = client.delete(f"/api/meetings/{meeting.id}", headers=auth_headers)
        assert response.status_code == 404


# ─── POST /api/meetings/{id}/reminders ───────────────────────────────────────

class TestCreateReminder:

    def test_create_reminder_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.post(
            f"/api/meetings/{meeting.id}/reminders",
            json={"reminder_type": "one_day"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["meeting_id"] == meeting.id
        assert data["reminder_type"] == "one_day"

    def test_create_reminder_invalid_type(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.post(
            f"/api/meetings/{meeting.id}/reminders",
            json={"reminder_type": "invalid_type"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_reminder_meeting_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.post(
            "/api/meetings/99999/reminders",
            json={"reminder_type": "one_day"},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ─── GET /api/meetings/{id}/reminders ────────────────────────────────────────

class TestListReminders:

    def test_list_reminders_empty(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.get(
            f"/api/meetings/{meeting.id}/reminders", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_reminders_after_create(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        client.post(
            f"/api/meetings/{meeting.id}/reminders",
            json={"reminder_type": "one_week"},
            headers=auth_headers,
        )
        client.post(
            f"/api/meetings/{meeting.id}/reminders",
            json={"reminder_type": "one_day"},
            headers=auth_headers,
        )

        response = client.get(
            f"/api/meetings/{meeting.id}/reminders", headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 2


# ─── Participants ─────────────────────────────────────────────────────────────

class TestParticipants:

    def test_list_participants_empty(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.get(
            f"/api/meetings/{meeting.id}/participants", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_add_participant(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.post(
            f"/api/meetings/{meeting.id}/participants",
            json={"name": "王五", "email": "wangwu@example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "王五"
        assert data["email"] == "wangwu@example.com"
        assert data["meeting_id"] == meeting.id

    def test_add_participant_duplicate_email_skipped(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """同一会议相同 email 不能重复添加。"""
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        client.post(
            f"/api/meetings/{meeting.id}/participants",
            json={"name": "李四", "email": "lisi@example.com"},
            headers=auth_headers,
        )
        response = client.post(
            f"/api/meetings/{meeting.id}/participants",
            json={"name": "李四（再次）", "email": "lisi@example.com"},
            headers=auth_headers,
        )
        # 应该返回 409 冲突
        assert response.status_code == 409

    def test_delete_participant(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        add_resp = client.post(
            f"/api/meetings/{meeting.id}/participants",
            json={"name": "赵六", "email": "zhaoliu@example.com"},
            headers=auth_headers,
        )
        pid = add_resp.json()["id"]

        del_resp = client.delete(
            f"/api/meetings/{meeting.id}/participants/{pid}",
            headers=auth_headers,
        )
        assert del_resp.status_code == 204

        list_resp = client.get(
            f"/api/meetings/{meeting.id}/participants", headers=auth_headers
        )
        assert list_resp.json() == []


# ─── Minutes ──────────────────────────────────────────────────────────────────

class TestMinutes:

    def test_get_minutes_empty(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        response = client.get(
            f"/api/meetings/{meeting.id}/minutes", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minutes"] is None or data["minutes"] == ""

    def test_update_and_get_minutes(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        committee = _create_committee(db_session, test_community.id)
        meeting = _create_meeting(db_session, test_community.id, committee.id)

        minutes_content = "## 会议纪要\n\n讨论了若干事项。"
        put_resp = client.put(
            f"/api/meetings/{meeting.id}/minutes",
            json={"minutes": minutes_content},
            headers=auth_headers,
        )
        assert put_resp.status_code == 200

        get_resp = client.get(
            f"/api/meetings/{meeting.id}/minutes", headers=auth_headers
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["minutes"] == minutes_content
