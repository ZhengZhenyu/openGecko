"""微信公众号文章统计数据模型。

支持按文章分类（版本发布/技术文章/活动）存储阅读量、
粉丝互动数据，以及多维度时间聚合统计。
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey,
    Enum as SAEnum, Date, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class WechatArticleStat(Base):
    """微信公众号文章每日统计快照。

    存储每篇已发布到微信的文章的每日阅读量、点赞、分享、
    评论、收藏、新增粉丝等互动数据。
    """
    __tablename__ = "wechat_article_stats"

    id = Column(Integer, primary_key=True, index=True)
    publish_record_id = Column(
        Integer,
        ForeignKey("publish_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 文章分类：release / technical / activity
    article_category = Column(
        SAEnum("release", "technical", "activity", name="article_category_enum"),
        nullable=False,
        default="technical",
        index=True,
    )
    # 统计日期（每日快照的日期）
    stat_date = Column(Date, nullable=False, index=True)

    # ── 阅读量指标 ──
    read_count = Column(Integer, default=0)           # 总阅读数
    read_user_count = Column(Integer, default=0)      # 阅读人数（去重）
    read_original_count = Column(Integer, default=0)  # 阅读原文数

    # ── 粉丝互动指标 ──
    like_count = Column(Integer, default=0)            # 点赞数
    wow_count = Column(Integer, default=0)             # 在看数
    share_count = Column(Integer, default=0)           # 分享数
    comment_count = Column(Integer, default=0)         # 评论数
    favorite_count = Column(Integer, default=0)        # 收藏数
    forward_count = Column(Integer, default=0)         # 转发数

    # ── 粉丝增长 ──
    new_follower_count = Column(Integer, default=0)    # 文章带来的新增关注
    unfollow_count = Column(Integer, default=0)        # 文章后取关数

    # ── 元数据 ──
    community_id = Column(
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collected_at = Column(DateTime, default=datetime.utcnow)

    # ── 关系 ──
    publish_record = relationship("PublishRecord", backref="wechat_stats")
    community = relationship("Community")

    __table_args__ = (
        # 每篇文章每天只保留一条记录
        UniqueConstraint("publish_record_id", "stat_date", name="uq_article_stat_date"),
        Index("ix_wechat_stats_category_date", "article_category", "stat_date"),
        Index("ix_wechat_stats_community_date", "community_id", "stat_date"),
    )

    def __repr__(self):
        return (
            f"<WechatArticleStat(publish_record_id={self.publish_record_id}, "
            f"date={self.stat_date}, reads={self.read_count})>"
        )


class WechatStatsAggregate(Base):
    """微信公众号统计聚合表。

    存储按天/周/月/季/半年/年维度预聚合的统计数据，
    便于前端快速展示折线图。
    """
    __tablename__ = "wechat_stats_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 聚合维度：daily / weekly / monthly / quarterly / semi_annual / annual
    period_type = Column(
        SAEnum(
            "daily", "weekly", "monthly", "quarterly",
            "semi_annual", "annual",
            name="period_type_enum",
        ),
        nullable=False,
        index=True,
    )
    # 时间段起始日期
    period_start = Column(Date, nullable=False, index=True)
    # 时间段结束日期
    period_end = Column(Date, nullable=False)
    # 文章分类（可为 NULL 表示全部分类汇总）
    article_category = Column(
        SAEnum("release", "technical", "activity", name="article_category_enum"),
        nullable=True,
        index=True,
    )

    # ── 汇总指标 ──
    total_articles = Column(Integer, default=0)
    total_read_count = Column(Integer, default=0)
    total_read_user_count = Column(Integer, default=0)
    total_like_count = Column(Integer, default=0)
    total_wow_count = Column(Integer, default=0)
    total_share_count = Column(Integer, default=0)
    total_comment_count = Column(Integer, default=0)
    total_favorite_count = Column(Integer, default=0)
    total_forward_count = Column(Integer, default=0)
    total_new_follower_count = Column(Integer, default=0)

    # ── 平均值指标 ──
    avg_read_count = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    community = relationship("Community")

    __table_args__ = (
        UniqueConstraint(
            "community_id", "period_type", "period_start", "article_category",
            name="uq_stats_aggregate",
        ),
        Index("ix_aggregate_period", "community_id", "period_type", "period_start"),
    )

    def __repr__(self):
        return (
            f"<WechatStatsAggregate(period={self.period_type}, "
            f"start={self.period_start}, category={self.article_category})>"
        )
