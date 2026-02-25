"""微信文章同步功能测试。

测试 sync_articles 和 sync_stats 端点，mock WeChat API 响应。
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest


# ── 同步文章 API 测试 ──


class TestSyncArticlesAPI:
    """POST /api/wechat-stats/sync/articles"""

    @patch("app.services.wechat_sync.wechat_service.fetch_published_articles", new_callable=AsyncMock)
    def test_sync_articles_success(
        self, mock_fetch, client, auth_headers, test_community, test_user
    ):
        """成功同步文章，创建 Content 和 PublishRecord。"""
        mock_fetch.return_value = {
            "total_count": 2,
            "item_count": 2,
            "item": [
                {
                    "article_id": "art_001",
                    "update_time": 1700000000,
                    "content": {
                        "news_item": [
                            {
                                "title": "测试文章一",
                                "url": "https://mp.weixin.qq.com/s/article1",
                                "thumb_url": "https://mmbiz.qpic.cn/cover1.jpg",
                            }
                        ]
                    },
                },
                {
                    "article_id": "art_002",
                    "update_time": 1700100000,
                    "content": {
                        "news_item": [
                            {
                                "title": "测试文章二",
                                "url": "https://mp.weixin.qq.com/s/article2",
                                "thumb_url": "",
                            }
                        ]
                    },
                },
            ],
        }

        resp = client.post("/api/wechat-stats/sync/articles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["synced"] == 2
        assert data["skipped"] == 0
        assert data["total"] == 2

    @patch("app.services.wechat_sync.wechat_service.fetch_published_articles", new_callable=AsyncMock)
    def test_sync_articles_skips_existing(
        self, mock_fetch, client, auth_headers, db_session, test_community, test_user
    ):
        """已存在的文章会跳过不重复创建。"""
        from app.models.content import Content
        from app.models.publish_record import PublishRecord

        # Pre-create a content + publish record
        content = Content(
            title="已有文章",
            community_id=test_community.id,
            created_by_user_id=test_user.id,
            owner_id=test_user.id,
            status="published",
        )
        db_session.add(content)
        db_session.flush()
        record = PublishRecord(
            content_id=content.id,
            channel="wechat",
            status="published",
            platform_url="https://mp.weixin.qq.com/s/existing",
            community_id=test_community.id,
        )
        db_session.add(record)
        db_session.commit()

        mock_fetch.return_value = {
            "total_count": 2,
            "item_count": 2,
            "item": [
                {
                    "article_id": "art_existing",
                    "update_time": 1700000000,
                    "content": {
                        "news_item": [
                            {
                                "title": "已有文章",
                                "url": "https://mp.weixin.qq.com/s/existing",
                            }
                        ]
                    },
                },
                {
                    "article_id": "art_new",
                    "update_time": 1700100000,
                    "content": {
                        "news_item": [
                            {
                                "title": "新文章",
                                "url": "https://mp.weixin.qq.com/s/new_one",
                            }
                        ]
                    },
                },
            ],
        }

        resp = client.post("/api/wechat-stats/sync/articles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["synced"] == 1
        assert data["skipped"] == 1

    @patch("app.services.wechat_sync.wechat_service.fetch_published_articles", new_callable=AsyncMock)
    def test_sync_articles_empty(self, mock_fetch, client, auth_headers):
        """微信端无文章时返回全零。"""
        mock_fetch.return_value = {"total_count": 0, "item_count": 0, "item": []}

        resp = client.post("/api/wechat-stats/sync/articles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["synced"] == 0
        assert data["skipped"] == 0
        assert data["total"] == 0

    @patch("app.services.wechat_sync.wechat_service.fetch_published_articles", new_callable=AsyncMock)
    def test_sync_articles_wechat_error(self, mock_fetch, client, auth_headers):
        """微信 API 报错时返回 502。"""
        mock_fetch.side_effect = Exception("获取已发布文章失败 [errcode=40001]: invalid credential")

        resp = client.post("/api/wechat-stats/sync/articles", headers=auth_headers)
        assert resp.status_code == 502
        assert "40001" in resp.json()["detail"]

    def test_sync_articles_no_auth(self, client, test_community):
        """未认证请求返回 401。"""
        resp = client.post(
            "/api/wechat-stats/sync/articles",
            headers={"X-Community-Id": str(test_community.id)},
        )
        assert resp.status_code == 401

    @patch("app.services.wechat_sync.wechat_service.fetch_published_articles", new_callable=AsyncMock)
    def test_sync_articles_multi_news_item(
        self, mock_fetch, client, auth_headers
    ):
        """多图文推送（一次推送多篇）每篇都创建。"""
        mock_fetch.return_value = {
            "total_count": 1,
            "item_count": 1,
            "item": [
                {
                    "article_id": "art_multi",
                    "update_time": 1700000000,
                    "content": {
                        "news_item": [
                            {"title": "主文章", "url": "https://mp.weixin.qq.com/s/main"},
                            {"title": "副文章", "url": "https://mp.weixin.qq.com/s/sub"},
                        ]
                    },
                },
            ],
        }

        resp = client.post("/api/wechat-stats/sync/articles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["synced"] == 2


# ── 同步统计 API 测试 ──


class TestSyncStatsAPI:
    """POST /api/wechat-stats/sync/stats"""

    @patch("app.services.wechat_sync.wechat_service.fetch_article_total_stats", new_callable=AsyncMock)
    def test_sync_stats_success(
        self, mock_fetch_stats, client, auth_headers, db_session, test_community, test_user
    ):
        """成功同步统计数据。"""
        from app.models.content import Content
        from app.models.publish_record import PublishRecord

        content = Content(
            title="统计测试文章",
            community_id=test_community.id,
            created_by_user_id=test_user.id,
            owner_id=test_user.id,
            status="published",
        )
        db_session.add(content)
        db_session.flush()
        record = PublishRecord(
            content_id=content.id,
            channel="wechat",
            status="published",
            platform_url="https://mp.weixin.qq.com/s/stats_test",
            community_id=test_community.id,
        )
        db_session.add(record)
        db_session.commit()

        mock_fetch_stats.return_value = {
            "list": [
                {
                    "ref_date": "2026-02-20",
                    "msgid": "msg_001",
                    "title": "统计测试文章",
                    "details": [
                        {
                            "stat_date": "2026-02-20",
                            "int_page_read_count": 500,
                            "int_page_read_user": 300,
                            "ori_page_read_count": 50,
                            "like_count": 20,
                            "wow_count": 10,
                            "share_count": 15,
                            "comment_count": 5,
                            "add_to_fav_count": 8,
                            "forward_count": 12,
                            "new_follower_count": 3,
                            "unfollow_count": 1,
                        }
                    ],
                }
            ]
        }

        resp = client.post(
            "/api/wechat-stats/sync/stats",
            json={"start_date": "2026-02-20", "end_date": "2026-02-20"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["days_processed"] == 1
        assert data["stats_written"] == 1

    def test_sync_stats_date_range_too_large(self, client, auth_headers):
        """日期范围超过30天返回 400。"""
        resp = client.post(
            "/api/wechat-stats/sync/stats",
            json={"start_date": "2026-01-01", "end_date": "2026-03-01"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "30" in resp.json()["detail"]

    def test_sync_stats_end_before_start(self, client, auth_headers):
        """结束日期早于开始日期返回 400。"""
        resp = client.post(
            "/api/wechat-stats/sync/stats",
            json={"start_date": "2026-02-20", "end_date": "2026-02-10"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @patch("app.services.wechat_sync.wechat_service.fetch_article_total_stats", new_callable=AsyncMock)
    def test_sync_stats_no_matching_article(
        self, mock_fetch_stats, client, auth_headers
    ):
        """找不到匹配文章时统计条数为 0。"""
        mock_fetch_stats.return_value = {
            "list": [
                {
                    "ref_date": "2026-02-20",
                    "msgid": "msg_999",
                    "title": "不存在的文章",
                    "details": [
                        {"stat_date": "2026-02-20", "int_page_read_count": 100, "int_page_read_user": 80}
                    ],
                }
            ]
        }

        resp = client.post(
            "/api/wechat-stats/sync/stats",
            json={"start_date": "2026-02-20", "end_date": "2026-02-20"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["days_processed"] == 1
        assert data["stats_written"] == 0

    def test_sync_stats_no_auth(self, client, test_community):
        """未认证请求返回 401。"""
        resp = client.post(
            "/api/wechat-stats/sync/stats",
            json={"start_date": "2026-02-20", "end_date": "2026-02-20"},
            headers={"X-Community-Id": str(test_community.id)},
        )
        assert resp.status_code == 401
