"""微信公众号文章同步服务。

从微信公众号拉取已发布文章列表和阅读统计数据，
写入 Content / PublishRecord / WechatArticleStat 表。
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.services.wechat import wechat_service
from app.services.wechat_stats import wechat_stats_service

_logger = get_logger(__name__)


class WechatSyncService:
    """编排微信文章与统计数据的同步。"""

    async def sync_articles(
        self, db: Session, community_id: int, user_id: int
    ) -> dict:
        """从微信公众号同步所有已发布文章。

        通过 freepublish/batchget 分页获取文章列表，
        为不存在的文章创建 Content + PublishRecord 记录。

        Returns:
            ``{"synced": int, "skipped": int, "total": int}``
        """
        synced = 0
        skipped = 0
        total_count = 0
        offset = 0
        page_size = 20

        while True:
            data = await wechat_service.fetch_published_articles(
                community_id, offset=offset, count=page_size
            )
            total_count = data.get("total_count", 0)
            items = data.get("item", [])

            if not items:
                break

            for item in items:
                article_id = item.get("article_id", "")
                update_time = item.get("update_time", 0)
                published_at = (
                    datetime.fromtimestamp(update_time, tz=UTC)
                    if update_time
                    else None
                )
                news_items = item.get("content", {}).get("news_item", [])

                for news in news_items:
                    title = news.get("title", "")
                    url = news.get("url", "")

                    if not title and not url:
                        continue

                    # Check if already exists by platform_url or platform_article_id
                    existing = None
                    if url:
                        existing = (
                            db.query(PublishRecord)
                            .filter(
                                PublishRecord.community_id == community_id,
                                PublishRecord.channel == "wechat",
                                PublishRecord.platform_url == url,
                            )
                            .first()
                        )
                    if not existing and article_id:
                        existing = (
                            db.query(PublishRecord)
                            .filter(
                                PublishRecord.community_id == community_id,
                                PublishRecord.channel == "wechat",
                                PublishRecord.platform_article_id == article_id,
                            )
                            .first()
                        )

                    if existing:
                        skipped += 1
                        continue

                    # Create Content record
                    content = Content(
                        title=title or "未命名微信文章",
                        content_markdown="",
                        content_html="",
                        source_type="contribution",
                        status="published",
                        community_id=community_id,
                        created_by_user_id=user_id,
                        owner_id=user_id,
                        cover_image=news.get("thumb_url", ""),
                    )
                    db.add(content)
                    db.flush()  # Get content.id

                    # Create PublishRecord
                    record = PublishRecord(
                        content_id=content.id,
                        channel="wechat",
                        status="published",
                        platform_article_id=article_id,
                        platform_url=url,
                        published_at=published_at,
                        community_id=community_id,
                    )
                    db.add(record)
                    synced += 1

            db.commit()

            offset += len(items)
            if offset >= total_count:
                break

        _logger.info(
            "微信文章同步完成",
            extra={
                "community_id": community_id,
                "synced": synced,
                "skipped": skipped,
                "total": total_count,
            },
        )
        return {"synced": synced, "skipped": skipped, "total": total_count}

    async def sync_stats(
        self,
        db: Session,
        community_id: int,
        start_date: date,
        end_date: date,
    ) -> dict:
        """从微信 datacube 同步文章阅读统计。

        逐天调用 getarticletotal，将数据写入 WechatArticleStat。

        Returns:
            ``{"days_processed": int, "stats_written": int}``
        """
        days_processed = 0
        stats_written = 0
        current = start_date

        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            try:
                data = await wechat_service.fetch_article_total_stats(
                    community_id, begin_date=date_str, end_date=date_str
                )
            except Exception as e:
                _logger.warning(
                    "获取统计数据失败，跳过该天",
                    extra={"date": date_str, "error": str(e)},
                )
                current += timedelta(days=1)
                days_processed += 1
                continue

            article_list = data.get("list", [])
            for article_data in article_list:
                title = article_data.get("title", "")
                msgid = article_data.get("msgid", "")

                # Find matching PublishRecord by title
                record = None
                if title:
                    record = (
                        db.query(PublishRecord)
                        .join(Content, PublishRecord.content_id == Content.id)
                        .filter(
                            PublishRecord.community_id == community_id,
                            PublishRecord.channel == "wechat",
                            Content.title == title,
                        )
                        .first()
                    )

                if not record:
                    _logger.debug(
                        "未找到匹配文章，跳过统计",
                        extra={"title": title, "msgid": msgid},
                    )
                    continue

                # Extract cumulative stats from details
                details = article_data.get("details", [])
                if not details:
                    continue

                # Use the last detail entry (most recent cumulative stats)
                detail = details[-1]
                stat_data = {
                    "publish_record_id": record.id,
                    "stat_date": current,
                    "article_category": "technical",  # default category
                    "read_count": detail.get("int_page_read_count", 0),
                    "read_user_count": detail.get("int_page_read_user", 0),
                    "read_original_count": detail.get("ori_page_read_count", 0),
                    "like_count": detail.get("like_count", 0),
                    "wow_count": detail.get("wow_count", 0),
                    "share_count": detail.get("share_count", 0),
                    "comment_count": detail.get("comment_count", 0),
                    "favorite_count": detail.get("add_to_fav_count", 0),
                    "forward_count": detail.get("forward_count", 0),
                    "new_follower_count": detail.get("new_follower_count", 0),
                    "unfollow_count": detail.get("unfollow_count", 0),
                }

                # Check if this record already has a category set
                from app.models.wechat_stats import WechatArticleStat

                existing_stat = (
                    db.query(WechatArticleStat)
                    .filter(
                        WechatArticleStat.publish_record_id == record.id,
                    )
                    .first()
                )
                if existing_stat:
                    stat_data["article_category"] = existing_stat.article_category

                wechat_stats_service.create_daily_stat(
                    db, data=stat_data, community_id=community_id
                )
                stats_written += 1

            days_processed += 1
            current += timedelta(days=1)

        _logger.info(
            "微信统计同步完成",
            extra={
                "community_id": community_id,
                "days_processed": days_processed,
                "stats_written": stats_written,
            },
        )
        return {"days_processed": days_processed, "stats_written": stats_written}


wechat_sync_service = WechatSyncService()
