"""微信公众号文章统计 API 测试。"""

from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.models.user import User
from app.models.wechat_stats import WechatArticleStat


# ── 测试专用 fixtures ──


@pytest.fixture(scope="function")
def wechat_content(db_session: Session, test_community: Community, test_user: User) -> Content:
    """创建一篇用于测试的内容。"""
    content = Content(
        title="测试微信文章",
        content_markdown="# 测试内容",
        community_id=test_community.id,
        created_by_user_id=test_user.id,
        owner_id=test_user.id,
        status="published",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    return content


@pytest.fixture(scope="function")
def wechat_publish_record(
    db_session: Session, wechat_content: Content, test_community: Community
) -> PublishRecord:
    """创建一条微信渠道的发布记录。"""
    record = PublishRecord(
        content_id=wechat_content.id,
        channel="wechat",
        status="published",
        community_id=test_community.id,
        published_at=datetime(2025, 1, 15, 10, 0, 0),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture(scope="function")
def wechat_stat(
    db_session: Session, wechat_publish_record: PublishRecord, test_community: Community
) -> WechatArticleStat:
    """创建一条微信文章每日统计记录。"""
    stat = WechatArticleStat(
        publish_record_id=wechat_publish_record.id,
        article_category="technical",
        stat_date=date(2025, 1, 15),
        read_count=1000,
        read_user_count=800,
        like_count=50,
        share_count=20,
        comment_count=10,
        community_id=test_community.id,
    )
    db_session.add(stat)
    db_session.commit()
    db_session.refresh(stat)
    return stat


# ── 每日统计录入 ──


class TestDailyStatCreate:
    """测试 POST /api/wechat-stats/daily-stats 端点。"""

    def test_create_daily_stat_success(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_publish_record: PublishRecord,
    ):
        """正常录入一条每日统计。"""
        payload = {
            "publish_record_id": wechat_publish_record.id,
            "stat_date": "2025-01-20",
            "article_category": "technical",
            "read_count": 500,
            "like_count": 30,
        }
        resp = client.post("/api/wechat-stats/daily-stats", json=payload, headers=auth_headers)
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert data["publish_record_id"] == wechat_publish_record.id
        assert data["read_count"] == 500
        assert data["like_count"] == 30
        assert data["stat_date"] == "2025-01-20"

    def test_create_daily_stat_upsert(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
        wechat_publish_record: PublishRecord,
    ):
        """对已有日期再次录入时应执行 upsert 更新。"""
        payload = {
            "publish_record_id": wechat_publish_record.id,
            "stat_date": "2025-01-15",
            "article_category": "technical",
            "read_count": 2000,
        }
        resp = client.post("/api/wechat-stats/daily-stats", json=payload, headers=auth_headers)
        assert resp.status_code == 201, resp.json()
        assert resp.json()["read_count"] == 2000

    def test_create_daily_stat_wrong_channel(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        wechat_content: Content,
        test_community: Community,
    ):
        """非 wechat 渠道的发布记录应返回 400。"""
        hugo_record = PublishRecord(
            content_id=wechat_content.id,
            channel="hugo",
            status="published",
            community_id=test_community.id,
        )
        db_session.add(hugo_record)
        db_session.commit()
        db_session.refresh(hugo_record)

        payload = {
            "publish_record_id": hugo_record.id,
            "stat_date": "2025-01-20",
            "article_category": "technical",
        }
        resp = client.post("/api/wechat-stats/daily-stats", json=payload, headers=auth_headers)
        assert resp.status_code == 400

    def test_create_daily_stat_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """发布记录不存在时应返回 404。"""
        payload = {
            "publish_record_id": 999999,
            "stat_date": "2025-01-20",
            "article_category": "technical",
        }
        resp = client.post("/api/wechat-stats/daily-stats", json=payload, headers=auth_headers)
        assert resp.status_code == 404

    def test_requires_auth(self, client: TestClient, wechat_publish_record: PublishRecord):
        """未认证时应返回 401。"""
        payload = {
            "publish_record_id": wechat_publish_record.id,
            "stat_date": "2025-01-20",
            "article_category": "technical",
        }
        resp = client.post("/api/wechat-stats/daily-stats", json=payload)
        assert resp.status_code == 401


# ── 批量录入 ──


class TestBatchDailyStats:
    """测试 POST /api/wechat-stats/daily-stats/batch 端点。"""

    def test_batch_create_success(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_publish_record: PublishRecord,
    ):
        """批量录入多条统计数据。"""
        payload = {
            "items": [
                {
                    "publish_record_id": wechat_publish_record.id,
                    "stat_date": "2025-02-01",
                    "article_category": "release",
                    "read_count": 300,
                },
                {
                    "publish_record_id": wechat_publish_record.id,
                    "stat_date": "2025-02-02",
                    "article_category": "release",
                    "read_count": 400,
                },
            ]
        }
        resp = client.post("/api/wechat-stats/daily-stats/batch", json=payload, headers=auth_headers)
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert len(data) == 2
        reads = {item["stat_date"]: item["read_count"] for item in data}
        assert reads["2025-02-01"] == 300
        assert reads["2025-02-02"] == 400

    def test_batch_empty_list(
        self, client: TestClient, auth_headers: dict
    ):
        """空列表应返回空数组。"""
        resp = client.post("/api/wechat-stats/daily-stats/batch", json={"items": []}, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json() == []


# ── 单篇文章每日统计查询 ──


class TestArticleDailyStats:
    """测试 GET /api/wechat-stats/articles/{id}/daily 端点。"""

    def test_get_article_daily_stats(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
        wechat_publish_record: PublishRecord,
    ):
        """获取指定文章的每日统计列表。"""
        resp = client.get(
            f"/api/wechat-stats/articles/{wechat_publish_record.id}/daily",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["read_count"] == 1000
        assert data[0]["stat_date"] == "2025-01-15"

    def test_get_article_daily_stats_with_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
        wechat_publish_record: PublishRecord,
    ):
        """日期范围过滤应正确返回数据。"""
        resp = client.get(
            f"/api/wechat-stats/articles/{wechat_publish_record.id}/daily",
            params={"start_date": "2025-01-10", "end_date": "2025-01-20"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_article_daily_stats_out_of_range(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
        wechat_publish_record: PublishRecord,
    ):
        """日期范围不覆盖数据时应返回空列表。"""
        resp = client.get(
            f"/api/wechat-stats/articles/{wechat_publish_record.id}/daily",
            params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_article_daily_stats_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """发布记录不存在时应返回 404。"""
        resp = client.get("/api/wechat-stats/articles/999999/daily", headers=auth_headers)
        assert resp.status_code == 404


# ── 文章分类更新 ──


class TestArticleCategoryUpdate:
    """测试 PUT /api/wechat-stats/articles/{id}/category 端点。"""

    def test_update_category_success(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
        wechat_publish_record: PublishRecord,
    ):
        """成功更新文章分类。"""
        resp = client.put(
            f"/api/wechat-stats/articles/{wechat_publish_record.id}/category",
            json={"article_category": "release"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["article_category"] == "release"
        assert data["updated"] >= 1

    def test_update_category_invalid_value(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_publish_record: PublishRecord,
    ):
        """无效分类值应返回 422。"""
        resp = client.put(
            f"/api/wechat-stats/articles/{wechat_publish_record.id}/category",
            json={"article_category": "invalid_category"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_update_category_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """发布记录不存在时应返回 404。"""
        resp = client.put(
            "/api/wechat-stats/articles/999999/category",
            json={"article_category": "release"},
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ── 统计概览 ──


class TestWechatStatsOverview:
    """测试 GET /api/wechat-stats/overview 端点。"""

    def test_get_overview_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """无数据时返回零值概览。"""
        resp = client.get("/api/wechat-stats/overview", headers=auth_headers)
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert "total_wechat_articles" in data
        assert "total_read_count" in data
        assert "category_summary" in data
        assert "top_articles" in data

    def test_get_overview_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """有数据时概览应包含正确统计信息。"""
        resp = client.get("/api/wechat-stats/overview", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # 应至少包含一个发布记录
        assert data["total_wechat_articles"] >= 1

    def test_overview_requires_auth(self, client: TestClient):
        """未认证时应返回 401。"""
        resp = client.get("/api/wechat-stats/overview")
        assert resp.status_code == 401


# ── 趋势数据 ──


class TestWechatStatsTrend:
    """测试 GET /api/wechat-stats/trend 端点。"""

    def test_get_trend_daily_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """无数据时应返回空 data_points。"""
        resp = client.get("/api/wechat-stats/trend", headers=auth_headers)
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert "period_type" in data
        assert "data_points" in data
        assert data["period_type"] == "daily"

    def test_get_trend_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """有数据时每日趋势应包含数据点。"""
        resp = client.get(
            "/api/wechat-stats/trend",
            params={"period_type": "daily", "start_date": "2025-01-01", "end_date": "2025-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data_points"]) >= 1
        point = data["data_points"][0]
        assert "date" in point
        assert "read_count" in point

    def test_get_trend_monthly(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """月维度趋势。"""
        resp = client.get(
            "/api/wechat-stats/trend",
            params={"period_type": "monthly"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["period_type"] == "monthly"

    def test_get_trend_invalid_period(
        self, client: TestClient, auth_headers: dict
    ):
        """无效 period_type 应返回 422。"""
        resp = client.get(
            "/api/wechat-stats/trend",
            params={"period_type": "invalid"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_get_trend_with_category_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """按分类过滤趋势数据。"""
        resp = client.get(
            "/api/wechat-stats/trend",
            params={"period_type": "daily", "category": "technical"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "technical"


# ── 文章排名 ──


class TestWechatStatsRanking:
    """测试 GET /api/wechat-stats/ranking 端点。"""

    def test_get_ranking_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """无数据时应返回空列表。"""
        resp = client.get("/api/wechat-stats/ranking", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_ranking_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """有数据时排名列表应包含正确字段。"""
        resp = client.get("/api/wechat-stats/ranking", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        item = data[0]
        assert "publish_record_id" in item
        assert "title" in item
        assert "read_count" in item
        assert "article_category" in item

    def test_get_ranking_with_category_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """按分类过滤排名。"""
        resp = client.get(
            "/api/wechat-stats/ranking",
            params={"category": "technical"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            assert item["article_category"] == "technical"

    def test_get_ranking_limit(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """limit 参数应正确限制返回数量。"""
        resp = client.get(
            "/api/wechat-stats/ranking",
            params={"limit": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) <= 1

    def test_get_ranking_requires_auth(self, client: TestClient):
        """未认证时应返回 401。"""
        resp = client.get("/api/wechat-stats/ranking")
        assert resp.status_code == 401


# ── 聚合重建 ──


class TestRebuildAggregates:
    """测试 POST /api/wechat-stats/aggregates/rebuild 端点。"""

    def test_rebuild_aggregates_no_data(
        self, client: TestClient, auth_headers: dict
    ):
        """无数据时重建应返回 rebuilt_count=0。"""
        resp = client.post("/api/wechat-stats/aggregates/rebuild", headers=auth_headers)
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert "rebuilt_count" in data
        assert "period_type" in data
        assert data["period_type"] == "daily"

    def test_rebuild_aggregates_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        wechat_stat: WechatArticleStat,
    ):
        """有数据时应成功重建聚合。"""
        resp = client.post(
            "/api/wechat-stats/aggregates/rebuild",
            params={
                "period_type": "daily",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["rebuilt_count"] >= 1

    def test_rebuild_aggregates_invalid_period(
        self, client: TestClient, auth_headers: dict
    ):
        """无效 period_type 应返回 422。"""
        resp = client.post(
            "/api/wechat-stats/aggregates/rebuild",
            params={"period_type": "bad_period"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_rebuild_aggregates_requires_auth(self, client: TestClient):
        """未认证时应返回 401。"""
        resp = client.post("/api/wechat-stats/aggregates/rebuild")
        assert resp.status_code == 401
