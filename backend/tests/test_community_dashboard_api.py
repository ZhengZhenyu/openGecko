"""
Tests for community dashboard API endpoints.

Endpoints tested:
- GET /api/communities/{community_id}/dashboard
- GET /api/communities/overview/stats  (superuser only)
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.channel import ChannelConfig
from app.models.committee import Committee
from app.models.community import Community
from app.models.content import Content
from app.models.event import Event
from app.models.meeting import Meeting
from app.models.publish_record import PublishRecord
from app.models.user import User, community_users


# ─── helpers ──────────────────────────────────────────────────────────────────

def _create_content(
    db_session: Session,
    community_id: int,
    owner_id: int,
    title: str = "测试文章",
    status: str = "draft",
) -> Content:
    c = Content(
        title=title,
        community_id=community_id,
        owner_id=owner_id,
        created_by_user_id=owner_id,
        status=status,
        work_status="in_progress",
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _create_committee(db_session: Session, community_id: int, slug: str = "tech") -> Committee:
    c = Committee(
        community_id=community_id,
        name="技术委员会",
        slug=slug,
        is_active=True,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _create_meeting(
    db_session: Session,
    community_id: int,
    committee_id: int,
    days_ahead: int = 3,
) -> Meeting:
    m = Meeting(
        community_id=community_id,
        committee_id=committee_id,
        title="即将召开的会议",
        scheduled_at=datetime.utcnow() + timedelta(days=days_ahead),
        duration=60,
        status="scheduled",
        work_status="planning",
        reminder_sent=False,
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


# ─── GET /api/communities/{id}/dashboard ─────────────────────────────────────

class TestCommunityDashboard:

    def test_dashboard_success_as_member(
        self,
        client: TestClient,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """社区成员可以访问工作台。"""
        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # 验证顶层结构
        assert "metrics" in data
        assert "monthly_trend" in data
        assert "channel_stats" in data
        assert "recent_contents" in data
        assert "upcoming_meetings" in data
        assert "calendar_events" in data

    def test_dashboard_success_as_superuser(
        self,
        client: TestClient,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        """超管可以访问任意社区工作台。"""
        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200

    def test_dashboard_metrics_structure(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        test_user: User,
        auth_headers: dict,
    ):
        """验证 metrics 包含 8 个正确字段。"""
        # 准备数据
        _create_content(db_session, test_community.id, test_user.id, status="draft")
        _create_content(db_session, test_community.id, test_user.id, status="published")
        _create_content(db_session, test_community.id, test_user.id, status="reviewing")

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        metrics = response.json()["metrics"]

        required_fields = [
            "total_contents",
            "published_contents",
            "reviewing_contents",
            "draft_contents",
            "total_members",
            "total_committees",
            "upcoming_meetings",
            "active_channels",
        ]
        for field in required_fields:
            assert field in metrics, f"指标字段 '{field}' 缺失"

        # 验证内容统计数值
        assert metrics["total_contents"] >= 3
        assert metrics["published_contents"] >= 1
        assert metrics["reviewing_contents"] >= 1
        assert metrics["draft_contents"] >= 1

    def test_dashboard_upcoming_meetings(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """upcoming_meetings 应包含未来的会议。"""
        committee = _create_committee(db_session, test_community.id)
        _create_meeting(db_session, test_community.id, committee.id, days_ahead=2)
        _create_meeting(db_session, test_community.id, committee.id, days_ahead=10)

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        upcoming = response.json()["upcoming_meetings"]
        assert len(upcoming) >= 2

    def test_dashboard_channel_stats(
        self,
        client: TestClient,
        db_session: Session,
        test_community: Community,
        auth_headers: dict,
    ):
        """channel_stats 应反映已配置渠道。"""
        cfg = ChannelConfig(
            channel="wechat",
            community_id=test_community.id,
            config={"app_id": "wx1"},
            enabled=True,
        )
        db_session.add(cfg)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        channel_stats = response.json()["channel_stats"]
        # channel_stats 是对象，包含 wechat/hugo/csdn/zhihu 键
        assert "wechat" in channel_stats
        assert "hugo" in channel_stats
        assert channel_stats["wechat"] >= 0

    def test_dashboard_community_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        response = client.get(
            "/api/communities/99999/dashboard",
            headers=auth_headers,
        )
        assert response.status_code in (403, 404)

    def test_dashboard_forbidden_for_non_member(
        self,
        client: TestClient,
        test_community: Community,
        another_user_auth_headers: dict,
    ):
        """非社区成员不能访问工作台。"""
        # another_user_auth_headers 属于 test_another_community，不属于 test_community
        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=another_user_auth_headers,
        )
        assert response.status_code == 403

    def test_dashboard_no_auth(
        self, client: TestClient, test_community: Community
    ):
        response = client.get(
            f"/api/communities/{test_community.id}/dashboard"
        )
        assert response.status_code == 401

    def test_dashboard_monthly_trend_structure(
        self,
        client: TestClient,
        test_community: Community,
        auth_headers: dict,
    ):
        """monthly_trend 的每个元素应包含 month 和 count 字段。"""
        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        trend = response.json()["monthly_trend"]
        assert isinstance(trend, list)
        # 应有 6 个月的数据（即使 count 都是 0）
        assert len(trend) >= 6
        for item in trend:
            assert "month" in item
            assert "count" in item


# ─── GET /api/communities/overview/stats ─────────────────────────────────────

class TestSuperuserOverviewStats:

    def test_overview_stats_success_as_superuser(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
    ):
        """超管可以访问全平台汇总数据。"""
        response = client.get(
            "/api/communities/overview/stats",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # 顶层字段验证
        assert "total_communities" in data
        assert "total_members" in data
        assert "total_contents" in data
        assert "communities" in data
        assert isinstance(data["communities"], list)

    def test_overview_stats_forbidden_for_regular_user(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """普通用户不能访问全平台汇总。"""
        response = client.get(
            "/api/communities/overview/stats",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_overview_stats_no_auth(self, client: TestClient):
        response = client.get("/api/communities/overview/stats")
        assert response.status_code == 401

    def test_overview_stats_community_list_structure(
        self,
        client: TestClient,
        test_community: Community,
        superuser_auth_headers: dict,
    ):
        """communities 列表中每个元素应含必要字段。"""
        response = client.get(
            "/api/communities/overview/stats",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
        communities = response.json()["communities"]
        assert len(communities) >= 1

        required = {"id", "name", "slug", "members_count", "contents_count"}
        for community_item in communities:
            for field in required:
                assert field in community_item, f"字段 '{field}' 缺失"


# ─── 覆盖率补充测试 ────────────────────────────────────────────────────────────

class TestCommunityDashboardCoverage:
    """补充覆盖各未覆盖代码路径。"""

    def test_community_not_found_as_superuser(
        self,
        client: TestClient,
        superuser_auth_headers: dict,
    ):
        """超管访问不存在的社区 → 404（覆盖 community_dashboard.py line 78）"""
        response = client.get(
            "/api/communities/99999/dashboard",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 404

    def test_monthly_trend_with_publish_records(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """有发布记录时月度趋势数据有值（覆盖 lines 178-180）"""
        # 创建内容与对应的发布记录
        content = Content(
            title="已发布文章",
            community_id=test_community.id,
            owner_id=test_user.id,
            created_by_user_id=test_user.id,
            status="published",
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        pr = PublishRecord(
            content_id=content.id,
            community_id=test_community.id,
            channel="wechat",
            status="published",
            published_at=datetime.utcnow(),
        )
        db_session.add(pr)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "monthly_trend" in data
        # 当月应有至少 1 条发布记录
        assert sum(m["count"] for m in data["monthly_trend"]) >= 1

    def test_recent_campaigns_active_in_response(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """存在 active 活动时 recent_campaigns 中有数据（覆盖 lines 251-255, 402-419）"""
        camp = Campaign(
            community_id=test_community.id,
            owner_id=test_user.id,
            name="推广活动",
            type="promotion",
            status="active",
        )
        db_session.add(camp)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "recent_campaigns" in data
        names = [c["name"] for c in data["recent_campaigns"]]
        assert "推广活动" in names

    def test_recent_campaigns_owner_name_populated(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """活动有 owner_id 时 owner_name 应填充（覆盖 lines 251-255 owner 分支）"""
        camp = Campaign(
            community_id=test_community.id,
            owner_id=test_user.id,
            name="有Owner的活动",
            type="community_care",
            status="draft",
        )
        db_session.add(camp)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        campaigns = data.get("recent_campaigns", [])
        targeted = next((c for c in campaigns if c["name"] == "有Owner的活动"), None)
        assert targeted is not None
        assert targeted["owner_name"] is not None

    def test_calendar_events_with_publish_record(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """日历中有发布事件（覆盖 lines 359-363）"""
        content = Content(
            title="日历发布文章",
            community_id=test_community.id,
            owner_id=test_user.id,
            created_by_user_id=test_user.id,
            status="published",
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        pr = PublishRecord(
            content_id=content.id,
            community_id=test_community.id,
            channel="wechat",
            status="published",
            published_at=datetime.utcnow(),
        )
        db_session.add(pr)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        publish_events = [
            e for e in data["calendar_events"] if e["type"] == "publish"
        ]
        assert len(publish_events) >= 1

    def test_calendar_events_scheduled_content(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """排期内容出现在日历中（覆盖 line 388）"""
        content = Content(
            title="排期待发文章",
            community_id=test_community.id,
            owner_id=test_user.id,
            created_by_user_id=test_user.id,
            status="draft",
            scheduled_publish_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        scheduled_events = [
            e for e in data["calendar_events"] if e["type"] == "scheduled"
        ]
        assert len(scheduled_events) >= 1

    def test_calendar_multi_day_event(
        self,
        client: TestClient,
        auth_headers: dict,
        test_community: Community,
        test_user: User,
        db_session: Session,
    ):
        """跨天活动在日历中生成多条记录（覆盖 lines 402-419）"""
        evt = Event(
            community_id=test_community.id,
            title="两日活动",
            event_type="offline",
            status="planning",
            planned_at=datetime.utcnow(),
            duration_hours=48.0,
        )
        db_session.add(evt)
        db_session.commit()

        response = client.get(
            f"/api/communities/{test_community.id}/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        event_entries = [
            e for e in data["calendar_events"] if e["resource_type"] == "event"
        ]
        # 48 小时活动应产生 2 个日历条目
        assert len(event_entries) >= 2
