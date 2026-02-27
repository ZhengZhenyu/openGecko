"""
Tests for personal dashboard API endpoints.

Endpoints tested:
- GET /api/dashboard/dashboard
- GET /api/dashboard/assigned/contents
- GET /api/dashboard/assigned/meetings
- PATCH /api/dashboard/contents/{content_id}/work-status
- PATCH /api/dashboard/meetings/{meeting_id}/work-status
- GET /api/dashboard/workload-overview
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.committee import Committee
from app.models.content import Content
from app.models.event import ChecklistItem, Event, EventTask
from app.models.meeting import Meeting
from app.models.user import User


def _create_committee(db_session, community, name="Test Committee"):
    import uuid
    committee = Committee(
        name=name,
        slug=f"committee-{uuid.uuid4().hex[:8]}",
        community_id=community.id,
    )
    db_session.add(committee)
    db_session.commit()
    db_session.refresh(committee)
    return committee


def _create_content(
    db_session,
    community,
    user,
    title="Test Content",
    work_status="planning",
    scheduled_publish_at=None,
):
    content = Content(
        title=title,
        content_markdown="Test markdown",
        community_id=community.id,
        source_type="contribution",
        work_status=work_status,
        scheduled_publish_at=scheduled_publish_at,
    )
    db_session.add(content)
    db_session.flush()
    content.assignees.append(user)
    db_session.commit()
    db_session.refresh(content)
    return content


def _create_meeting(
    db_session,
    community,
    user,
    title="Test Meeting",
    status="scheduled",
    scheduled_at=None,
):
    committee = _create_committee(db_session, community)
    if scheduled_at is None:
        scheduled_at = datetime(2025, 6, 1, 10, 0)
    meeting = Meeting(
        title=title,
        community_id=community.id,
        committee_id=committee.id,
        scheduled_at=scheduled_at,
        duration=60,
        status=status,
    )
    db_session.add(meeting)
    db_session.flush()
    meeting.assignees.append(user)
    db_session.commit()
    db_session.refresh(meeting)
    return meeting


class TestGetDashboard:
    """Tests for GET /api/dashboard/dashboard"""

    def test_dashboard_empty(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test dashboard returns empty data when no assignments."""
        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "contents" in data
        assert "meetings" in data
        assert "content_stats" in data
        assert "meeting_stats" in data
        assert data["total_assigned_items"] == 0

    def test_dashboard_with_assigned_content(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test dashboard returns assigned content."""
        _create_content(db_session, test_community, test_user, "My Content")

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_assigned_items"] >= 1
        content_titles = [c["title"] for c in data["contents"]]
        assert "My Content" in content_titles

    def test_dashboard_with_assigned_meeting(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test dashboard returns assigned meetings."""
        _create_meeting(db_session, test_community, test_user, "Team Sync")

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_assigned_items"] >= 1
        meeting_titles = [m["title"] for m in data["meetings"]]
        assert "Team Sync" in meeting_titles

    def test_dashboard_stats_calculation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test dashboard statistics are calculated correctly."""
        _create_content(db_session, test_community, test_user, "Planning", "planning")
        _create_content(db_session, test_community, test_user, "In Progress", "in_progress")
        _create_content(db_session, test_community, test_user, "Done", "completed")

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        stats = data["content_stats"]
        assert stats["planning"] >= 1
        assert stats["in_progress"] >= 1
        assert stats["completed"] >= 1


class TestGetAssignedContents:
    """Tests for GET /api/dashboard/assigned/contents"""

    def test_get_assigned_contents_empty(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test returns empty list when no assigned contents."""
        response = client.get("/api/users/me/assigned/contents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_assigned_contents_with_data(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test returns assigned contents."""
        _create_content(db_session, test_community, test_user, "Content A")
        _create_content(db_session, test_community, test_user, "Content B")

        response = client.get("/api/users/me/assigned/contents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        titles = [item["title"] for item in data]
        assert "Content A" in titles
        assert "Content B" in titles

    def test_get_assigned_contents_filter_by_work_status(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test filter by work_status works."""
        _create_content(db_session, test_community, test_user, "Planning Content", "planning")
        _create_content(db_session, test_community, test_user, "Done Content", "completed")

        response = client.get(
            "/api/users/me/assigned/contents?work_status=planning",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["work_status"] == "planning" for item in data)


class TestGetAssignedMeetings:
    """Tests for GET /api/dashboard/assigned/meetings"""

    def test_get_assigned_meetings_empty(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test returns empty list when no assigned meetings."""
        response = client.get("/api/users/me/assigned/meetings", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_assigned_meetings_with_data(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test returns assigned meetings."""
        _create_meeting(db_session, test_community, test_user, "Meeting A")
        _create_meeting(db_session, test_community, test_user, "Meeting B")

        response = client.get("/api/users/me/assigned/meetings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_assigned_meetings_filter_by_work_status(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test filter by work_status maps to meeting status."""
        _create_meeting(db_session, test_community, test_user, "Scheduled", "scheduled")
        _create_meeting(db_session, test_community, test_user, "Completed", "completed")

        response = client.get(
            "/api/users/me/assigned/meetings?work_status=planning",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # All returned should be from 'scheduled' status mapped to 'planning'
        assert all(item["work_status"] == "planning" for item in data)


class TestUpdateContentWorkStatus:
    """Tests for PATCH /api/dashboard/contents/{content_id}/work-status"""

    def test_update_content_work_status_as_assignee(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test assignee can update work status."""
        content = _create_content(db_session, test_community, test_user, "My Task")

        response = client.patch(
            f"/api/users/me/contents/{content.id}/work-status",
            json={"work_status": "in_progress"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["work_status"] == "in_progress"
        assert data["old_status"] == "planning"

    def test_update_content_work_status_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating non-existent content returns 404."""
        response = client.patch(
            "/api/users/me/contents/99999/work-status",
            json={"work_status": "in_progress"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_content_work_status_not_authorized(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test non-assignee cannot update work status."""
        # Create content without assigning test_user
        content = Content(
            title="Other Person's Task",
            content_markdown="Test",
            community_id=test_community.id,
            source_type="contribution",
        )
        db_session.add(content)
        db_session.commit()

        response = client.patch(
            f"/api/users/me/contents/{content.id}/work-status",
            json={"work_status": "in_progress"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_content_work_status_all_values(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test all valid work_status values can be set."""
        content = _create_content(db_session, test_community, test_user)

        for status in ["planning", "in_progress", "completed"]:
            response = client.patch(
                f"/api/users/me/contents/{content.id}/work-status",
                json={"work_status": status},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["work_status"] == status


class TestUpdateMeetingWorkStatus:
    """Tests for PATCH /api/dashboard/meetings/{meeting_id}/work-status"""

    def test_update_meeting_work_status_as_assignee(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test assignee can update meeting work status."""
        meeting = _create_meeting(db_session, test_community, test_user)

        response = client.patch(
            f"/api/users/me/meetings/{meeting.id}/work-status",
            json={"work_status": "in_progress"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["work_status"] == "in_progress"
        assert data["status"] == "in_progress"

    def test_update_meeting_work_status_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating non-existent meeting returns 404."""
        response = client.patch(
            "/api/users/me/meetings/99999/work-status",
            json={"work_status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_meeting_work_status_not_authorized(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """Test non-assignee cannot update meeting work status."""
        committee = _create_committee(db_session, test_community)
        meeting = Meeting(
            title="Other Meeting",
            community_id=test_community.id,
            committee_id=committee.id,
            scheduled_at=datetime(2025, 6, 1, 10, 0),
            duration=60,
            status="scheduled",
        )
        db_session.add(meeting)
        db_session.commit()

        response = client.patch(
            f"/api/users/me/meetings/{meeting.id}/work-status",
            json={"work_status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_meeting_work_status_completed(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Test setting meeting work_status to completed maps to 'completed' status."""
        meeting = _create_meeting(db_session, test_community, test_user)

        response = client.patch(
            f"/api/users/me/meetings/{meeting.id}/work-status",
            json={"work_status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


class TestGetWorkloadOverview:
    """Tests for GET /api/dashboard/workload-overview"""

    def test_workload_overview_requires_superuser(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test workload overview requires superuser access."""
        response = client.get("/api/users/me/workload-overview", headers=auth_headers)
        # test_user is admin (not superuser) - should be 403
        assert response.status_code == 403

    def test_workload_overview_as_superuser(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        """Test superuser can access workload overview."""
        response = client.get("/api/users/me/workload-overview", headers=superuser_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)


class TestOverdueStatsCalculation:
    """Tests for overdue detection in content_stats and meeting_stats.

    The `overdue` counter increments when:
      - work_status != 'completed'  AND
      - deadline is set  AND
      - deadline < now
    """

    # ── Content overdue tests ──────────────────────────────────────────────

    def test_overdue_field_present_in_dashboard_stats(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """The `overdue` key must be present in both content_stats and meeting_stats."""
        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "overdue" in data["content_stats"]
        assert "overdue" in data["meeting_stats"]

    def test_content_past_deadline_not_completed_is_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Non-completed content with a past deadline is counted as overdue."""
        past = datetime.utcnow() - timedelta(days=3)
        _create_content(
            db_session, test_community, test_user, "Overdue Task", "in_progress", past
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["content_stats"]
        assert stats["overdue"] >= 1

    def test_completed_content_with_past_deadline_not_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Completed content is never overdue even if deadline has passed."""
        past = datetime.utcnow() - timedelta(days=3)
        _create_content(
            db_session, test_community, test_user, "Done Task", "completed", past
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["content_stats"]
        # completed items should not bump overdue
        assert stats["overdue"] == 0

    def test_content_without_deadline_not_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Content with no deadline is never overdue."""
        _create_content(
            db_session, test_community, test_user, "No Deadline Task", "planning", None
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["content_stats"]
        assert stats["overdue"] == 0

    def test_content_with_future_deadline_not_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Content whose deadline is in the future is not overdue."""
        future = datetime.utcnow() + timedelta(days=7)
        _create_content(
            db_session, test_community, test_user, "Future Task", "in_progress", future
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["content_stats"]
        assert stats["overdue"] == 0

    def test_overdue_count_matches_qualifying_items(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Exactly N qualifying items raise overdue count by N."""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=7)
        # 2 overdue
        _create_content(db_session, test_community, test_user, "Overdue 1", "planning", past)
        _create_content(db_session, test_community, test_user, "Overdue 2", "in_progress", past)
        # 1 not overdue (future)
        _create_content(db_session, test_community, test_user, "Not Yet", "planning", future)
        # 1 not overdue (completed + past)
        _create_content(db_session, test_community, test_user, "Done", "completed", past)

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["content_stats"]
        assert stats["overdue"] == 2

    # ── Meeting overdue tests ──────────────────────────────────────────────

    def test_meeting_past_scheduled_not_completed_is_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Non-completed meeting whose scheduled_at has passed counts as overdue."""
        past = datetime.utcnow() - timedelta(days=2)
        _create_meeting(
            db_session, test_community, test_user, "Overdue Meeting", "scheduled", past
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["meeting_stats"]
        assert stats["overdue"] >= 1

    def test_completed_meeting_with_past_scheduled_not_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Completed meeting is never considered overdue."""
        past = datetime.utcnow() - timedelta(days=2)
        _create_meeting(
            db_session, test_community, test_user, "Done Meeting", "completed", past
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["meeting_stats"]
        assert stats["overdue"] == 0

    def test_future_meeting_not_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """Meeting scheduled in the future is not overdue."""
        future = datetime.utcnow() + timedelta(days=5)
        _create_meeting(
            db_session, test_community, test_user, "Upcoming Meeting", "scheduled", future
        )

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()["meeting_stats"]
        assert stats["overdue"] == 0

    # ── Workload overview overdue tests ────────────────────────────────────

    def test_workload_overview_user_entry_has_overdue_fields(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        superuser_auth_headers: dict,
    ):
        """Each user entry in workload overview has overdue in content_stats and meeting_stats."""
        past = datetime.utcnow() - timedelta(days=1)
        _create_content(db_session, test_community, test_user, "Admin Overdue", "planning", past)

        response = client.get("/api/users/me/workload-overview", headers=superuser_auth_headers)
        assert response.status_code == 200
        users = response.json()["users"]
        # At least the test_user should appear (has an assigned content)
        assert len(users) >= 1
        for user_entry in users:
            assert "overdue" in user_entry["content_stats"]
            assert "overdue" in user_entry["meeting_stats"]

    def test_workload_overview_overdue_count_reflects_assignments(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        superuser_auth_headers: dict,
    ):
        """Overdue count for a user correctly reflects their overdue content."""
        past = datetime.utcnow() - timedelta(days=5)
        future = datetime.utcnow() + timedelta(days=5)
        _create_content(db_session, test_community, test_user, "Late Task", "in_progress", past)
        _create_content(db_session, test_community, test_user, "On Time Task", "planning", future)

        response = client.get("/api/users/me/workload-overview", headers=superuser_auth_headers)
        assert response.status_code == 200
        users = response.json()["users"]
        # Find the test_user entry by looking for users with any overdue > 0
        user_entries = [u for u in users if u["content_stats"]["overdue"] > 0]
        assert len(user_entries) >= 1
        # The overdue user should have exactly 1 overdue content item
        assert user_entries[0]["content_stats"]["overdue"] == 1


# ─── CampaignTask 在工作台的覆盖率测试 ──────────────────────────────────────────

class TestCampaignTasksInDashboard:
    """覆盖 dashboard.py 中未覆盖的 CampaignTask / ChecklistItem 路径。"""

    def test_dashboard_with_campaign_tasks(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """用户被分配运营活动任务时工作台应返回任务列表（覆盖 lines 123-124, 155-156）"""
        from app.models.campaign import Campaign, CampaignTask

        camp = Campaign(
            community_id=test_community.id,
            owner_id=test_user.id,
            name="工作台测试活动",
            type="promotion",
            status="active",
        )
        db_session.add(camp)
        db_session.commit()
        db_session.refresh(camp)

        task = CampaignTask(
            campaign_id=camp.id,
            title="工作台测试任务",
            status="in_progress",
            priority="high",
            assignee_ids=[test_user.id],
        )
        db_session.add(task)
        db_session.commit()

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "campaign_tasks" in data
        assert len(data["campaign_tasks"]) >= 1
        ct = data["campaign_tasks"][0]
        assert ct["title"] == "工作台测试任务"
        assert ct["campaign_name"] == "工作台测试活动"

    def test_dashboard_with_event_task_assigned(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """用户被分配 EventTask 时工作台中应有 event_tasks 且 event_title 填充
        （覆盖 lines 88-89：event_ids 非空时的额外 Event 名称预查询）"""
        evt = Event(
            community_id=test_community.id,
            title="任务所属活动",
            event_type="offline",
            status="planning",
        )
        db_session.add(evt)
        db_session.commit()
        db_session.refresh(evt)

        et = EventTask(
            event_id=evt.id,
            title="个人工作台事件任务",
            status="not_started",
            assignee_ids=[test_user.id],
        )
        db_session.add(et)
        db_session.commit()

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "event_tasks" in data
        assert len(data["event_tasks"]) >= 1
        assert data["event_tasks"][0]["event_title"] == "任务所属活动"

    def test_dashboard_with_checklist_item_extra_event_lookup(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """有清单项且该清单项所属活动与 EventTask 活动不同时，触发额外事件名称查询
        （覆盖 lines 88-89）"""
        # 创建活动以附加清单项（无 EventTask，确保 checklist_event_ids 非空）
        evt = Event(
            community_id=test_community.id,
            title="清单测试活动",
            event_type="offline",
            status="planning",
        )
        db_session.add(evt)
        db_session.commit()
        db_session.refresh(evt)

        item = ChecklistItem(
            event_id=evt.id,
            phase="pre",
            title="清单测试项",
            assignee_ids=[test_user.id],
        )
        db_session.add(item)
        db_session.commit()

        response = client.get("/api/users/me/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "checklist_items" in data
        assert len(data["checklist_items"]) >= 1
        assert data["checklist_items"][0]["event_title"] == "清单测试活动"

    def test_workload_overview_with_campaign_and_event_tasks(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """工作负载概览中包含运营活动任务与活动清单项统计（覆盖 lines 422, 432-458, 515-551）"""
        from app.models.campaign import Campaign, CampaignTask

        # 创建 Meeting 并分配给 test_user（覆盖 line 422：meeting_rows 循环）
        meeting = _create_meeting(db_session, test_community, test_user, "工作负载会议")

        # 创建 EventTask 分配给 test_user
        evt = Event(
            community_id=test_community.id,
            title="工作负载测试活动",
            event_type="offline",
            status="planning",
        )
        db_session.add(evt)
        db_session.commit()
        db_session.refresh(evt)

        et = EventTask(
            event_id=evt.id,
            title="工作负载事件任务",
            status="in_progress",
            assignee_ids=[test_user.id],
            end_date=(datetime.utcnow() - timedelta(days=3)).date(),  # 逾期：覆盖 lines 550-551
        )
        db_session.add(et)

        # 创建 ChecklistItem 分配给 test_user
        checklist = ChecklistItem(
            event_id=evt.id,
            phase="pre",
            title="工作负载清单项",
            assignee_ids=[test_user.id],
        )
        db_session.add(checklist)

        # 创建 CampaignTask 分配给 test_user
        camp = Campaign(
            community_id=test_community.id,
            owner_id=test_user.id,
            name="工作负载活动",
            type="promotion",
            status="active",
        )
        db_session.add(camp)
        db_session.commit()
        db_session.refresh(camp)

        ct = CampaignTask(
            campaign_id=camp.id,
            title="工作负载活动任务",
            status="in_progress",
            priority="medium",
            assignee_ids=[test_user.id],
        )
        db_session.add(ct)
        db_session.commit()

        response = client.get("/api/users/me/workload-overview", headers=superuser_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data

        # 找到 test_user 的条目
        user_entry = next(
            (u for u in data["users"] if u["user_id"] == test_user.id), None
        )
        assert user_entry is not None, "test_user 应出现在工作负载概览中"

        # campaign_task_stats 应有非零统计
        ct_stats = user_entry["campaign_task_stats"]
        assert ct_stats["in_progress"] >= 1

        # event_task_stats 应有非零统计
        et_stats = user_entry["event_task_stats"]
        assert et_stats["in_progress"] >= 1

        # checklist_item_stats 应有非零统计
        cl_stats = user_entry["checklist_item_stats"]
        assert cl_stats["planning"] >= 1

        # meeting_stats 应有统计（meeting loop line 422）
        m_stats = user_entry["meeting_stats"]
        assert m_stats["planning"] >= 1 or m_stats["in_progress"] >= 1
