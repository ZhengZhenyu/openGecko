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
