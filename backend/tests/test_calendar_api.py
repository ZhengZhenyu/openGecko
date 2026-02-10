"""
Tests for content calendar API endpoints.

Endpoints tested:
- GET /api/contents/calendar/events
- PATCH /api/contents/{content_id}/schedule
- POST /api/contents (scheduled_publish_at support)
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.content import Content


class TestCalendarEvents:
    """Tests for GET /api/contents/calendar/events"""

    def test_get_calendar_events_with_scheduled(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """已排期内容应当出现在日历事件中"""
        now = datetime.utcnow()
        content = Content(
            title="Scheduled Post",
            content_markdown="# Test",
            content_html="<h1>Test</h1>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
            scheduled_publish_at=now + timedelta(days=3),
        )
        db_session.add(content)
        db_session.commit()

        start = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        end = (now + timedelta(days=30)).strftime("%Y-%m-%d")

        response = client.get(
            f"/api/contents/calendar/events?start={start}&end={end}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(item["title"] == "Scheduled Post" for item in data)

    def test_get_calendar_events_unscheduled_in_range(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """未排期但在日期范围内创建的内容也应出现"""
        content = Content(
            title="Unscheduled Post",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
            scheduled_publish_at=None,
        )
        db_session.add(content)
        db_session.commit()

        now = datetime.utcnow()
        start = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        end = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        response = client.get(
            f"/api/contents/calendar/events?start={start}&end={end}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert any(item["title"] == "Unscheduled Post" for item in data)

    def test_get_calendar_events_out_of_range(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """排期在范围之外的内容不应出现"""
        now = datetime.utcnow()
        content = Content(
            title="Far Future",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
            scheduled_publish_at=now + timedelta(days=200),
        )
        db_session.add(content)
        db_session.commit()

        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=30)).strftime("%Y-%m-%d")

        response = client.get(
            f"/api/contents/calendar/events?start={start}&end={end}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert not any(item["title"] == "Far Future" for item in data)

    def test_get_calendar_events_filter_by_status(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """状态筛选应正常工作"""
        now = datetime.utcnow()
        for status in ["draft", "approved"]:
            db_session.add(
                Content(
                    title=f"{status} event",
                    content_markdown="t",
                    content_html="<p>t</p>",
                    author="A",
                    community_id=test_community.id,
                    source_type="contribution",
                    status=status,
                    scheduled_publish_at=now + timedelta(days=1),
                )
            )
        db_session.commit()

        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        response = client.get(
            f"/api/contents/calendar/events?start={start}&end={end}&status=draft",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "draft" for item in data)

    def test_get_calendar_events_invalid_date(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """无效日期格式应返回 400"""
        response = client.get(
            "/api/contents/calendar/events?start=bad-date&end=2026-03-01",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_get_calendar_events_requires_auth(
        self,
        client: TestClient,
    ):
        """未认证请求应返回 401/403"""
        response = client.get(
            "/api/contents/calendar/events?start=2026-02-01&end=2026-03-01"
        )
        assert response.status_code in [401, 403]

    def test_get_calendar_events_community_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_another_community: Community,
        auth_headers: dict,
    ):
        """社区隔离：只能看到自己社区的数据"""
        now = datetime.utcnow()
        db_session.add(
            Content(
                title="Other Community Event",
                content_markdown="t",
                content_html="<p>t</p>",
                author="A",
                community_id=test_another_community.id,
                source_type="contribution",
                scheduled_publish_at=now + timedelta(days=1),
            )
        )
        db_session.commit()

        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        response = client.get(
            f"/api/contents/calendar/events?start={start}&end={end}",
            headers=auth_headers,
        )
        data = response.json()
        assert not any(item["title"] == "Other Community Event" for item in data)

    def test_get_calendar_events_response_fields(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """验证返回字段结构符合 ContentCalendarOut schema"""
        now = datetime.utcnow()
        db_session.add(
            Content(
                title="Field Check",
                content_markdown="md",
                content_html="<p>md</p>",
                author="Bob",
                category="tech",
                community_id=test_community.id,
                source_type="release_note",
                status="reviewing",
                scheduled_publish_at=now + timedelta(days=2),
            )
        )
        db_session.commit()

        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        response = client.get(
            f"/api/contents/calendar/events?start={start}&end={end}",
            headers=auth_headers,
        )
        data = response.json()
        item = next(i for i in data if i["title"] == "Field Check")

        required_fields = {"id", "title", "status", "source_type", "author", "category", "scheduled_publish_at", "created_at"}
        assert required_fields.issubset(set(item.keys()))
        assert item["status"] == "reviewing"
        assert item["source_type"] == "release_note"
        assert item["author"] == "Bob"
        assert item["category"] == "tech"


class TestUpdateContentSchedule:
    """Tests for PATCH /api/contents/{content_id}/schedule"""

    def test_update_schedule_success(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user,
        auth_headers: dict,
    ):
        """正常设置排期时间"""
        content = Content(
            title="To Schedule",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
            owner_id=test_user.id,
        )
        db_session.add(content)
        db_session.commit()

        new_time = "2026-02-20T10:00:00"
        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            json={"scheduled_publish_at": new_time},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scheduled_publish_at"] is not None
        assert "2026-02-20" in data["scheduled_publish_at"]

    def test_remove_schedule(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user,
        auth_headers: dict,
    ):
        """取消排期（设为 null）"""
        content = Content(
            title="Scheduled",
            content_markdown="Test",
            content_html="<p>Test</p>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
            owner_id=test_user.id,
            scheduled_publish_at=datetime(2026, 3, 1, 10, 0),
        )
        db_session.add(content)
        db_session.commit()

        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            json={"scheduled_publish_at": None},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["scheduled_publish_at"] is None

    def test_update_schedule_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """内容不存在应返回 404"""
        response = client.patch(
            "/api/contents/99999/schedule",
            json={"scheduled_publish_at": "2026-03-01T10:00:00"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_schedule_requires_auth(
        self,
        client: TestClient,
    ):
        """未认证请求应返回 401/403"""
        response = client.patch(
            "/api/contents/1/schedule",
            json={"scheduled_publish_at": "2026-03-01T10:00:00"},
        )
        assert response.status_code in [401, 403]

    def test_update_schedule_returns_full_content(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user,
        auth_headers: dict,
    ):
        """更新排期应返回完整的 ContentOut 响应"""
        content = Content(
            title="Full Response Check",
            content_markdown="# Markdown",
            content_html="<h1>Markdown</h1>",
            author="Author",
            community_id=test_community.id,
            source_type="contribution",
            owner_id=test_user.id,
        )
        db_session.add(content)
        db_session.commit()

        response = client.patch(
            f"/api/contents/{content.id}/schedule",
            json={"scheduled_publish_at": "2026-02-20T10:00:00"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # 验证 ContentOut 必要字段
        assert "id" in data
        assert "title" in data
        assert "content_markdown" in data
        assert "content_html" in data
        assert "status" in data
        assert "community_id" in data


class TestCreateContentWithSchedule:
    """Tests for POST /api/contents (scheduled_publish_at support)"""

    def test_create_content_with_schedule(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """创建内容时可携带排期时间"""
        response = client.post(
            "/api/contents",
            json={
                "title": "Scheduled New",
                "content_markdown": "# Hello",
                "source_type": "contribution",
                "author": "Tester",
                "scheduled_publish_at": "2026-02-25T14:00:00",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["scheduled_publish_at"] is not None
        assert "2026-02-25" in data["scheduled_publish_at"]

    def test_create_content_without_schedule(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """创建内容时不带排期仍然正常"""
        response = client.post(
            "/api/contents",
            json={
                "title": "No Schedule",
                "content_markdown": "# Hello",
                "source_type": "contribution",
                "author": "Tester",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["scheduled_publish_at"] is None

    def test_create_content_schedule_appears_in_calendar(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """创建带排期的内容后，日历事件 API 能查到"""
        # 创建
        create_resp = client.post(
            "/api/contents",
            json={
                "title": "Calendar Visible",
                "content_markdown": "test",
                "source_type": "contribution",
                "author": "A",
                "scheduled_publish_at": "2026-02-18T09:00:00",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201

        # 查询日历
        cal_resp = client.get(
            "/api/contents/calendar/events?start=2026-02-01&end=2026-03-01",
            headers=auth_headers,
        )
        assert cal_resp.status_code == 200
        data = cal_resp.json()
        assert any(item["title"] == "Calendar Visible" for item in data)
