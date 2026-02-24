"""微信公众号文章统计服务。

提供每日统计采集、多维度聚合计算、趋势数据查询等功能。
"""

from datetime import date, timedelta

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.timezone import utc_now
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.models.wechat_stats import WechatArticleStat, WechatStatsAggregate

# ── 分类标签映射 ──

CATEGORY_LABELS = {
    "release": "版本发布",
    "technical": "技术文章",
    "activity": "活动",
}


class WechatStatsService:
    """微信公众号统计服务。"""

    # ── 每日统计 CRUD ──

    def create_daily_stat(
        self, db: Session, *, data: dict, community_id: int
    ) -> WechatArticleStat:
        """创建或更新某篇文章某天的统计。"""
        existing = db.query(WechatArticleStat).filter(
            WechatArticleStat.publish_record_id == data["publish_record_id"],
            WechatArticleStat.stat_date == data["stat_date"],
        ).first()

        if existing:
            for key, value in data.items():
                if key not in ("publish_record_id", "stat_date"):
                    setattr(existing, key, value)
            existing.collected_at = utc_now()
            db.commit()
            db.refresh(existing)
            return existing

        stat = WechatArticleStat(
            **data,
            community_id=community_id,
        )
        db.add(stat)
        db.commit()
        db.refresh(stat)
        return stat

    def batch_create_daily_stats(
        self, db: Session, *, items: list[dict], community_id: int
    ) -> list[WechatArticleStat]:
        """批量创建/更新每日统计。"""
        results = []
        for item in items:
            stat = self.create_daily_stat(db, data=item, community_id=community_id)
            results.append(stat)
        return results

    def get_article_daily_stats(
        self,
        db: Session,
        *,
        publish_record_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[WechatArticleStat]:
        """获取某篇文章的每日统计列表。"""
        query = db.query(WechatArticleStat).filter(
            WechatArticleStat.publish_record_id == publish_record_id
        )
        if start_date:
            query = query.filter(WechatArticleStat.stat_date >= start_date)
        if end_date:
            query = query.filter(WechatArticleStat.stat_date <= end_date)
        return query.order_by(WechatArticleStat.stat_date).all()

    # ── 文章分类更新 ──

    def update_article_category(
        self,
        db: Session,
        *,
        publish_record_id: int,
        category: str,
    ) -> int:
        """更新某篇文章所有统计记录的分类。返回更新行数。"""
        rows = db.query(WechatArticleStat).filter(
            WechatArticleStat.publish_record_id == publish_record_id
        ).update({"article_category": category})
        db.commit()
        return rows

    # ── 概览 ──

    def get_overview(self, db: Session, *, community_id: int) -> dict:
        """获取微信统计概览数据。"""
        total_wechat = db.query(PublishRecord).filter(
            PublishRecord.community_id == community_id,
            PublishRecord.channel == "wechat",
            PublishRecord.status.in_(["draft", "published"]),
        ).count()

        latest_date_subq = db.query(
            func.max(WechatArticleStat.stat_date)
        ).filter(
            WechatArticleStat.community_id == community_id
        ).scalar()

        total_read = 0
        total_interaction = 0
        category_summary = []

        if latest_date_subq:
            cat_stats = db.query(
                WechatArticleStat.article_category,
                func.count(WechatArticleStat.id).label("article_count"),
                func.sum(WechatArticleStat.read_count).label("total_read"),
                func.sum(WechatArticleStat.like_count).label("total_like"),
                func.sum(WechatArticleStat.share_count).label("total_share"),
                func.sum(WechatArticleStat.comment_count).label("total_comment"),
            ).filter(
                WechatArticleStat.community_id == community_id,
                WechatArticleStat.stat_date == latest_date_subq,
            ).group_by(
                WechatArticleStat.article_category
            ).all()

            for cat, count, reads, likes, shares, comments in cat_stats:
                reads = reads or 0
                likes = likes or 0
                shares = shares or 0
                comments = comments or 0
                total_read += reads
                total_interaction += likes + shares + comments
                category_summary.append({
                    "category": cat,
                    "category_label": CATEGORY_LABELS.get(cat, cat),
                    "article_count": count,
                    "total_read_count": reads,
                    "total_like_count": likes,
                    "total_share_count": shares,
                    "total_comment_count": comments,
                    "avg_read_count": reads // count if count else 0,
                })

        top_articles = []
        if latest_date_subq:
            rows = db.query(
                WechatArticleStat,
                Content.title,
                Content.id.label("content_id"),
                PublishRecord.published_at,
            ).join(
                PublishRecord,
                WechatArticleStat.publish_record_id == PublishRecord.id,
            ).join(
                Content,
                PublishRecord.content_id == Content.id,
            ).filter(
                WechatArticleStat.community_id == community_id,
                WechatArticleStat.stat_date == latest_date_subq,
            ).order_by(
                WechatArticleStat.read_count.desc()
            ).limit(10).all()

            for stat, title, content_id, published_at in rows:
                top_articles.append({
                    "publish_record_id": stat.publish_record_id,
                    "content_id": content_id,
                    "title": title,
                    "article_category": stat.article_category,
                    "read_count": stat.read_count,
                    "like_count": stat.like_count,
                    "share_count": stat.share_count,
                    "comment_count": stat.comment_count,
                    "published_at": published_at.isoformat() if published_at else None,
                })

        return {
            "total_wechat_articles": total_wechat,
            "total_read_count": total_read,
            "total_interaction_count": total_interaction,
            "category_summary": category_summary,
            "top_articles": top_articles,
        }

    # ── 趋势数据 ──

    def get_trend(
        self,
        db: Session,
        *,
        community_id: int,
        period_type: str = "daily",
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """获取趋势折线图数据。"""
        query = db.query(WechatStatsAggregate).filter(
            WechatStatsAggregate.community_id == community_id,
            WechatStatsAggregate.period_type == period_type,
        )
        if category:
            query = query.filter(WechatStatsAggregate.article_category == category)
        else:
            query = query.filter(WechatStatsAggregate.article_category.is_(None))

        if start_date:
            query = query.filter(WechatStatsAggregate.period_start >= start_date)
        if end_date:
            query = query.filter(WechatStatsAggregate.period_end <= end_date)

        aggregates = query.order_by(WechatStatsAggregate.period_start).all()

        if aggregates:
            data_points = []
            for agg in aggregates:
                label = self._period_label(agg.period_type, agg.period_start)
                data_points.append({
                    "date": label,
                    "read_count": agg.total_read_count,
                    "read_user_count": agg.total_read_user_count,
                    "like_count": agg.total_like_count,
                    "wow_count": agg.total_wow_count,
                    "share_count": agg.total_share_count,
                    "comment_count": agg.total_comment_count,
                    "favorite_count": agg.total_favorite_count,
                    "forward_count": agg.total_forward_count,
                    "new_follower_count": agg.total_new_follower_count,
                })
            return {"period_type": period_type, "category": category, "data_points": data_points}

        if period_type == "daily":
            return self._compute_daily_trend(
                db, community_id=community_id, category=category,
                start_date=start_date, end_date=end_date,
            )

        return self._compute_period_trend(
            db, community_id=community_id, period_type=period_type,
            category=category, start_date=start_date, end_date=end_date,
        )

    def _compute_daily_trend(
        self, db: Session, *, community_id: int, category: str | None,
        start_date: date | None, end_date: date | None,
    ) -> dict:
        """从原始表计算每日趋势。"""
        query = db.query(
            WechatArticleStat.stat_date,
            func.sum(WechatArticleStat.read_count).label("read_count"),
            func.sum(WechatArticleStat.read_user_count).label("read_user_count"),
            func.sum(WechatArticleStat.like_count).label("like_count"),
            func.sum(WechatArticleStat.wow_count).label("wow_count"),
            func.sum(WechatArticleStat.share_count).label("share_count"),
            func.sum(WechatArticleStat.comment_count).label("comment_count"),
            func.sum(WechatArticleStat.favorite_count).label("favorite_count"),
            func.sum(WechatArticleStat.forward_count).label("forward_count"),
            func.sum(WechatArticleStat.new_follower_count).label("new_follower_count"),
        ).filter(WechatArticleStat.community_id == community_id)

        if category:
            query = query.filter(WechatArticleStat.article_category == category)
        if start_date:
            query = query.filter(WechatArticleStat.stat_date >= start_date)
        if end_date:
            query = query.filter(WechatArticleStat.stat_date <= end_date)

        rows = query.group_by(WechatArticleStat.stat_date).order_by(WechatArticleStat.stat_date).all()

        data_points = []
        for row in rows:
            data_points.append({
                "date": row.stat_date.isoformat(),
                "read_count": row.read_count or 0,
                "read_user_count": row.read_user_count or 0,
                "like_count": row.like_count or 0,
                "wow_count": row.wow_count or 0,
                "share_count": row.share_count or 0,
                "comment_count": row.comment_count or 0,
                "favorite_count": row.favorite_count or 0,
                "forward_count": row.forward_count or 0,
                "new_follower_count": row.new_follower_count or 0,
            })

        return {"period_type": "daily", "category": category, "data_points": data_points}

    def _compute_period_trend(
        self, db: Session, *, community_id: int, period_type: str,
        category: str | None, start_date: date | None, end_date: date | None,
    ) -> dict:
        """从原始每日数据聚合出周/月/季/半年/年趋势。"""
        daily_result = self._compute_daily_trend(
            db, community_id=community_id, category=category,
            start_date=start_date, end_date=end_date,
        )

        if not daily_result["data_points"]:
            return {"period_type": period_type, "category": category, "data_points": []}

        buckets: dict[str, dict] = {}
        for dp in daily_result["data_points"]:
            d = date.fromisoformat(dp["date"])
            bucket_key = self._get_bucket_key(d, period_type)

            if bucket_key not in buckets:
                buckets[bucket_key] = {
                    "date": bucket_key,
                    "read_count": 0, "read_user_count": 0, "like_count": 0,
                    "wow_count": 0, "share_count": 0, "comment_count": 0,
                    "favorite_count": 0, "forward_count": 0, "new_follower_count": 0,
                }
            b = buckets[bucket_key]
            for field in [
                "read_count", "read_user_count", "like_count", "wow_count",
                "share_count", "comment_count", "favorite_count",
                "forward_count", "new_follower_count",
            ]:
                b[field] += dp[field]

        data_points = sorted(buckets.values(), key=lambda x: x["date"])
        return {"period_type": period_type, "category": category, "data_points": data_points}

    # ── 聚合计算 ──

    def rebuild_aggregates(
        self, db: Session, *, community_id: int, period_type: str = "daily",
        start_date: date | None = None, end_date: date | None = None,
    ) -> int:
        """重建聚合数据。返回更新/创建的记录数。"""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        categories = [None, "release", "technical", "activity"]
        count = 0

        for cat in categories:
            trend = self._compute_daily_trend(
                db, community_id=community_id, category=cat,
                start_date=start_date, end_date=end_date,
            )
            if not trend["data_points"]:
                continue

            buckets: dict[str, list] = {}
            for dp in trend["data_points"]:
                d = date.fromisoformat(dp["date"])
                bucket_key = self._get_bucket_key(d, period_type)
                if bucket_key not in buckets:
                    buckets[bucket_key] = []
                buckets[bucket_key].append(dp)

            for bucket_key, points in buckets.items():
                period_start_d = self._bucket_key_to_start(bucket_key, period_type)
                period_end_d = self._bucket_key_to_end(period_start_d, period_type)

                totals = {
                    "total_read_count": sum(p["read_count"] for p in points),
                    "total_read_user_count": sum(p["read_user_count"] for p in points),
                    "total_like_count": sum(p["like_count"] for p in points),
                    "total_wow_count": sum(p["wow_count"] for p in points),
                    "total_share_count": sum(p["share_count"] for p in points),
                    "total_comment_count": sum(p["comment_count"] for p in points),
                    "total_favorite_count": sum(p["favorite_count"] for p in points),
                    "total_forward_count": sum(p["forward_count"] for p in points),
                    "total_new_follower_count": sum(p["new_follower_count"] for p in points),
                }
                total_articles = len(points)
                avg_read = totals["total_read_count"] // total_articles if total_articles else 0

                cat_filter = (
                    WechatStatsAggregate.article_category == cat
                    if cat else WechatStatsAggregate.article_category.is_(None)
                )
                existing = db.query(WechatStatsAggregate).filter(
                    WechatStatsAggregate.community_id == community_id,
                    WechatStatsAggregate.period_type == period_type,
                    WechatStatsAggregate.period_start == period_start_d,
                    cat_filter,
                ).first()

                if existing:
                    existing.period_end = period_end_d
                    existing.total_articles = total_articles
                    existing.avg_read_count = avg_read
                    for k, v in totals.items():
                        setattr(existing, k, v)
                else:
                    agg = WechatStatsAggregate(
                        community_id=community_id,
                        period_type=period_type,
                        period_start=period_start_d,
                        period_end=period_end_d,
                        article_category=cat,
                        total_articles=total_articles,
                        avg_read_count=avg_read,
                        **totals,
                    )
                    db.add(agg)
                count += 1

        db.commit()
        return count

    # ── 文章排行榜 ──

    def get_article_ranking(
        self, db: Session, *, community_id: int,
        category: str | None = None, limit: int = 100,
    ) -> list[dict]:
        """获取最新前 N 篇文章的统计排名。"""
        latest_subq = db.query(
            WechatArticleStat.publish_record_id,
            func.max(WechatArticleStat.stat_date).label("max_date"),
        ).filter(
            WechatArticleStat.community_id == community_id,
        ).group_by(WechatArticleStat.publish_record_id).subquery()

        query = db.query(
            WechatArticleStat,
            Content.title,
            Content.id.label("content_id"),
            PublishRecord.published_at,
        ).join(
            latest_subq,
            and_(
                WechatArticleStat.publish_record_id == latest_subq.c.publish_record_id,
                WechatArticleStat.stat_date == latest_subq.c.max_date,
            ),
        ).join(
            PublishRecord,
            WechatArticleStat.publish_record_id == PublishRecord.id,
        ).join(
            Content,
            PublishRecord.content_id == Content.id,
        ).filter(WechatArticleStat.community_id == community_id)

        if category:
            query = query.filter(WechatArticleStat.article_category == category)

        rows = query.order_by(WechatArticleStat.read_count.desc()).limit(limit).all()

        result = []
        for stat, title, content_id, published_at in rows:
            result.append({
                "publish_record_id": stat.publish_record_id,
                "content_id": content_id,
                "title": title,
                "article_category": stat.article_category,
                "read_count": stat.read_count,
                "like_count": stat.like_count,
                "share_count": stat.share_count,
                "comment_count": stat.comment_count,
                "published_at": published_at.isoformat() if published_at else None,
            })
        return result

    # ── 工具方法 ──

    @staticmethod
    def _period_label(period_type: str, d: date) -> str:
        if period_type == "daily":
            return d.isoformat()
        elif period_type == "weekly":
            iso = d.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        elif period_type == "monthly":
            return d.strftime("%Y-%m")
        elif period_type == "quarterly":
            q = (d.month - 1) // 3 + 1
            return f"{d.year}-Q{q}"
        elif period_type == "semi_annual":
            h = 1 if d.month <= 6 else 2
            return f"{d.year}-H{h}"
        elif period_type == "annual":
            return str(d.year)
        return d.isoformat()

    @staticmethod
    def _get_bucket_key(d: date, period_type: str) -> str:
        if period_type == "daily":
            return d.isoformat()
        elif period_type == "weekly":
            iso = d.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        elif period_type == "monthly":
            return d.strftime("%Y-%m")
        elif period_type == "quarterly":
            q = (d.month - 1) // 3 + 1
            return f"{d.year}-Q{q}"
        elif period_type == "semi_annual":
            h = 1 if d.month <= 6 else 2
            return f"{d.year}-H{h}"
        elif period_type == "annual":
            return str(d.year)
        return d.isoformat()

    @staticmethod
    def _bucket_key_to_start(key: str, period_type: str) -> date:
        if period_type == "daily":
            return date.fromisoformat(key)
        elif period_type == "weekly":
            year, week = key.split("-W")
            return date.fromisocalendar(int(year), int(week), 1)
        elif period_type == "monthly":
            return date.fromisoformat(key + "-01")
        elif period_type == "quarterly":
            year, q = key.split("-Q")
            month = (int(q) - 1) * 3 + 1
            return date(int(year), month, 1)
        elif period_type == "semi_annual":
            year, h = key.split("-H")
            month = 1 if h == "1" else 7
            return date(int(year), month, 1)
        elif period_type == "annual":
            return date(int(key), 1, 1)
        return date.fromisoformat(key)

    @staticmethod
    def _bucket_key_to_end(start: date, period_type: str) -> date:
        if period_type == "daily":
            return start
        elif period_type == "weekly":
            return start + timedelta(days=6)
        elif period_type == "monthly":
            if start.month == 12:
                return date(start.year + 1, 1, 1) - timedelta(days=1)
            return date(start.year, start.month + 1, 1) - timedelta(days=1)
        elif period_type == "quarterly":
            month = start.month + 3
            year = start.year + (1 if month > 12 else 0)
            month = month - 12 if month > 12 else month
            return date(year, month, 1) - timedelta(days=1)
        elif period_type == "semi_annual":
            month = start.month + 6
            year = start.year + (1 if month > 12 else 0)
            month = month - 12 if month > 12 else month
            return date(year, month, 1) - timedelta(days=1)
        elif period_type == "annual":
            return date(start.year, 12, 31)
        return start


wechat_stats_service = WechatStatsService()
