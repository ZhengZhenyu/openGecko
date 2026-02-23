"""微信公众号统计服务单元测试。

补充 test_wechat_stats_api.py 中未覆盖的 Service 层逻辑。
"""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.models.user import User
from app.models.wechat_stats import WechatArticleStat, WechatStatsAggregate
from app.services.wechat_stats import WechatStatsService


# ── Fixtures ──


@pytest.fixture(scope="function")
def service() -> WechatStatsService:
    """微信统计服务实例。"""
    return WechatStatsService()


@pytest.fixture(scope="function")
def test_data(
    db_session: Session,
    test_community: Community,
    test_user: User,
) -> tuple[Content, PublishRecord, WechatArticleStat]:
    """创建测试数据：内容、发布记录、多条每日统计。"""
    content = Content(
        title="测试文章",
        content_markdown="# 测试",
        community_id=test_community.id,
        created_by_user_id=test_user.id,
        owner_id=test_user.id,
        status="published",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    record = PublishRecord(
        content_id=content.id,
        channel="wechat",
        status="published",
        community_id=test_community.id,
        published_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    # 创建多条每日统计
    stats = []
    for i in range(5):
        stat = WechatArticleStat(
            publish_record_id=record.id,
            article_category="technical",
            stat_date=date(2025, 1, 10 + i),
            read_count=100 * (i + 1),
            read_user_count=80 * (i + 1),
            like_count=5 * (i + 1),
            wow_count=2 * (i + 1),
            share_count=3 * (i + 1),
            comment_count=1 * (i + 1),
            favorite_count=1 * (i + 1),
            forward_count=2 * (i + 1),
            new_follower_count=10 * (i + 1),
            community_id=test_community.id,
        )
        db_session.add(stat)
        stats.append(stat)
    db_session.commit()

    return content, record, stats[0]


# ── 工具方法测试 ──


class TestPeriodLabel:
    """测试 _period_label 静态方法。"""

    def test_daily_label(self, service: WechatStatsService):
        """每日标签应为 ISO 日期。"""
        d = date(2025, 1, 15)
        assert service._period_label("daily", d) == "2025-01-15"

    def test_weekly_label(self, service: WechatStatsService):
        """周标签应为 ISO 周格式。"""
        d = date(2025, 1, 15)
        assert service._period_label("weekly", d) == "2025-W03"

    def test_monthly_label(self, service: WechatStatsService):
        """月标签应为 YYYY-MM 格式。"""
        d = date(2025, 1, 15)
        assert service._period_label("monthly", d) == "2025-01"

    def test_quarterly_label(self, service: WechatStatsService):
        """季度标签应为 YYYY-QN 格式。"""
        d = date(2025, 1, 15)
        assert service._period_label("quarterly", d) == "2025-Q1"
        d2 = date(2025, 4, 15)
        assert service._period_label("quarterly", d2) == "2025-Q2"

    def test_semi_annual_label(self, service: WechatStatsService):
        """半年标签应为 YYYY-HN 格式。"""
        d = date(2025, 1, 15)
        assert service._period_label("semi_annual", d) == "2025-H1"
        d2 = date(2025, 7, 15)
        assert service._period_label("semi_annual", d2) == "2025-H2"

    def test_annual_label(self, service: WechatStatsService):
        """年标签应为 YYYY 格式。"""
        d = date(2025, 1, 15)
        assert service._period_label("annual", d) == "2025"


class TestGetBucketKey:
    """测试 _get_bucket_key 静态方法。"""

    def test_daily_bucket(self, service: WechatStatsService):
        """每日桶键应为 ISO 日期。"""
        d = date(2025, 1, 15)
        assert service._get_bucket_key(d, "daily") == "2025-01-15"

    def test_weekly_bucket(self, service: WechatStatsService):
        """周桶键应为 ISO 周格式。"""
        d = date(2025, 1, 15)
        assert service._get_bucket_key(d, "weekly") == "2025-W03"

    def test_monthly_bucket(self, service: WechatStatsService):
        """月桶键应为 YYYY-MM 格式。"""
        d = date(2025, 1, 15)
        assert service._get_bucket_key(d, "monthly") == "2025-01"

    def test_quarterly_bucket(self, service: WechatStatsService):
        """季度桶键应为 YYYY-QN 格式。"""
        d = date(2025, 1, 15)
        assert service._get_bucket_key(d, "quarterly") == "2025-Q1"

    def test_semi_annual_bucket(self, service: WechatStatsService):
        """半年桶键应为 YYYY-HN 格式。"""
        d = date(2025, 1, 15)
        assert service._get_bucket_key(d, "semi_annual") == "2025-H1"

    def test_annual_bucket(self, service: WechatStatsService):
        """年桶键应为 YYYY 格式。"""
        d = date(2025, 1, 15)
        assert service._get_bucket_key(d, "annual") == "2025"


class TestBucketKeyToStart:
    """测试 _bucket_key_to_start 静态方法。"""

    def test_daily_to_start(self, service: WechatStatsService):
        """每日桶键转开始日期。"""
        key = "2025-01-15"
        assert service._bucket_key_to_start(key, "daily") == date(2025, 1, 15)

    def test_weekly_to_start(self, service: WechatStatsService):
        """周桶键转开始日期（周一）。"""
        key = "2025-W03"
        result = service._bucket_key_to_start(key, "weekly")
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 13  # 2025年第3周周一

    def test_monthly_to_start(self, service: WechatStatsService):
        """月桶键转开始日期（月初）。"""
        key = "2025-01"
        assert service._bucket_key_to_start(key, "monthly") == date(2025, 1, 1)

    def test_quarterly_to_start(self, service: WechatStatsService):
        """季度桶键转开始日期。"""
        key = "2025-Q2"
        assert service._bucket_key_to_start(key, "quarterly") == date(2025, 4, 1)

    def test_semi_annual_to_start(self, service: WechatStatsService):
        """半年桶键转开始日期。"""
        key = "2025-H2"
        assert service._bucket_key_to_start(key, "semi_annual") == date(2025, 7, 1)

    def test_annual_to_start(self, service: WechatStatsService):
        """年桶键转开始日期。"""
        key = "2025"
        assert service._bucket_key_to_start(key, "annual") == date(2025, 1, 1)


class TestBucketKeyToEnd:
    """测试 _bucket_key_to_end 静态方法。"""

    def test_daily_to_end(self, service: WechatStatsService):
        """每日桶键转结束日期。"""
        start = date(2025, 1, 15)
        assert service._bucket_key_to_end(start, "daily") == date(2025, 1, 15)

    def test_weekly_to_end(self, service: WechatStatsService):
        """周桶键转结束日期（周日）。"""
        start = date(2025, 1, 13)
        assert service._bucket_key_to_end(start, "weekly") == date(2025, 1, 19)

    def test_monthly_to_end(self, service: WechatStatsService):
        """月桶键转结束日期（月末）。"""
        start = date(2025, 1, 1)
        assert service._bucket_key_to_end(start, "monthly") == date(2025, 1, 31)

    def test_monthly_to_end_december(self, service: WechatStatsService):
        """12月月末跨年。"""
        start = date(2025, 12, 1)
        assert service._bucket_key_to_end(start, "monthly") == date(2025, 12, 31)

    def test_quarterly_to_end(self, service: WechatStatsService):
        """季度桶键转结束日期。"""
        start = date(2025, 1, 1)
        assert service._bucket_key_to_end(start, "quarterly") == date(2025, 3, 31)

    def test_semi_annual_to_end(self, service: WechatStatsService):
        """半年桶键转结束日期。"""
        start = date(2025, 1, 1)
        assert service._bucket_key_to_end(start, "semi_annual") == date(2025, 6, 30)

    def test_annual_to_end(self, service: WechatStatsService):
        """年桶键转结束日期。"""
        start = date(2025, 1, 1)
        assert service._bucket_key_to_end(start, "annual") == date(2025, 12, 31)


# ── 趋势数据测试 ──


class TestGetTrendWithAggregates:
    """测试 get_trend 使用聚合数据的情况。"""

    def test_get_trend_uses_aggregates(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """当存在聚合数据时，应优先使用聚合数据。"""
        content, record, _ = test_data

        # 创建聚合数据
        agg = WechatStatsAggregate(
            community_id=test_community.id,
            period_type="daily",
            period_start=date(2025, 1, 10),
            period_end=date(2025, 1, 10),
            article_category=None,
            total_articles=1,
            avg_read_count=100,
            total_read_count=100,
            total_read_user_count=80,
            total_like_count=5,
            total_wow_count=2,
            total_share_count=3,
            total_comment_count=1,
            total_favorite_count=1,
            total_forward_count=2,
            total_new_follower_count=10,
        )
        db_session.add(agg)
        db_session.commit()

        result = service.get_trend(
            db_session,
            community_id=test_community.id,
            period_type="daily",
        )

        assert result["period_type"] == "daily"
        assert result["category"] is None
        assert len(result["data_points"]) == 1
        assert result["data_points"][0]["read_count"] == 100


class TestComputePeriodTrend:
    """测试 _compute_period_trend 方法。"""

    def test_compute_weekly_trend(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """测试周趋势聚合。"""
        result = service._compute_period_trend(
            db_session,
            community_id=test_community.id,
            period_type="weekly",
            category=None,
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 14),
        )

        assert result["period_type"] == "weekly"
        assert len(result["data_points"]) >= 1

    def test_compute_monthly_trend(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """测试月趋势聚合。"""
        result = service._compute_period_trend(
            db_session,
            community_id=test_community.id,
            period_type="monthly",
            category=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        assert result["period_type"] == "monthly"
        assert len(result["data_points"]) >= 1

    def test_compute_quarterly_trend(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """测试季度趋势聚合。"""
        result = service._compute_period_trend(
            db_session,
            community_id=test_community.id,
            period_type="quarterly",
            category=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )

        assert result["period_type"] == "quarterly"
        assert len(result["data_points"]) >= 1


# ── 聚合数据重建测试 ──


class TestRebuildAggregates:
    """测试 rebuild_aggregates 方法。"""

    def test_rebuild_daily_aggregates(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """重建每日聚合数据。"""
        count = service.rebuild_aggregates(
            db_session,
            community_id=test_community.id,
            period_type="daily",
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 14),
        )

        assert count >= 1

        # 验证聚合数据已创建
        aggs = db_session.query(WechatStatsAggregate).filter(
            WechatStatsAggregate.community_id == test_community.id,
            WechatStatsAggregate.period_type == "daily",
        ).all()
        assert len(aggs) >= 1

    def test_rebuild_updates_existing(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """重建时应更新已有聚合数据。"""
        # 先创建聚合数据
        service.rebuild_aggregates(
            db_session,
            community_id=test_community.id,
            period_type="daily",
            start_date=date(2025, 1, 10),
        )

        # 再次重建（应更新而非创建）
        count = service.rebuild_aggregates(
            db_session,
            community_id=test_community.id,
            period_type="daily",
            start_date=date(2025, 1, 10),
        )

        assert count >= 1

    def test_rebuild_with_category(
        self,
        db_session: Session,
        service: WechatStatsService,
        test_community: Community,
        test_data: tuple[Content, PublishRecord, WechatArticleStat],
    ):
        """重建指定分类的聚合数据。"""
        count = service.rebuild_aggregates(
            db_session,
            community_id=test_community.id,
            period_type="daily",
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 14),
        )

        assert count >= 1

        # 验证分类聚合数据
        aggs = db_session.query(WechatStatsAggregate).filter(
            WechatStatsAggregate.community_id == test_community.id,
            WechatStatsAggregate.period_type == "daily",
            WechatStatsAggregate.article_category == "technical",
        ).all()
        assert len(aggs) >= 1
