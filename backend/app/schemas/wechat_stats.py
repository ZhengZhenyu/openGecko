"""微信公众号文章统计相关 Pydantic Schema。"""

from datetime import date, datetime

from pydantic import BaseModel, Field

# ── 文章分类 ──

class ArticleCategoryUpdate(BaseModel):
    """更新文章分类请求。"""
    article_category: str = Field(
        ...,
        description="文章分类: release(版本发布), technical(技术文章), activity(活动)",
        pattern="^(release|technical|activity)$",
    )


# ── 每日统计 ──

class WechatArticleStatOut(BaseModel):
    """单篇文章每日统计输出。"""
    id: int
    publish_record_id: int
    article_category: str
    stat_date: date
    read_count: int
    read_user_count: int
    read_original_count: int
    like_count: int
    wow_count: int
    share_count: int
    comment_count: int
    favorite_count: int
    forward_count: int
    new_follower_count: int
    unfollow_count: int
    collected_at: datetime

    model_config = {"from_attributes": True}


class WechatDailyStatCreate(BaseModel):
    """手动录入/采集每日统计数据。"""
    publish_record_id: int
    article_category: str = Field(
        default="technical",
        pattern="^(release|technical|activity)$",
    )
    stat_date: date
    read_count: int = 0
    read_user_count: int = 0
    read_original_count: int = 0
    like_count: int = 0
    wow_count: int = 0
    share_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    forward_count: int = 0
    new_follower_count: int = 0
    unfollow_count: int = 0


class WechatDailyStatBatchCreate(BaseModel):
    """批量录入每日统计数据。"""
    items: list[WechatDailyStatCreate]


# ── 聚合统计 ──

class WechatStatsAggregateOut(BaseModel):
    """聚合统计输出。"""
    id: int
    community_id: int
    period_type: str
    period_start: date
    period_end: date
    article_category: str | None
    total_articles: int
    total_read_count: int
    total_read_user_count: int
    total_like_count: int
    total_wow_count: int
    total_share_count: int
    total_comment_count: int
    total_favorite_count: int
    total_forward_count: int
    total_new_follower_count: int
    avg_read_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── 图表数据 ──

class TrendDataPoint(BaseModel):
    """折线图数据点。"""
    date: str = Field(description="日期标签，例如 '2026-02-01' 或 '2026-W05'")
    read_count: int = 0
    read_user_count: int = 0
    like_count: int = 0
    wow_count: int = 0
    share_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    forward_count: int = 0
    new_follower_count: int = 0


class TrendResponse(BaseModel):
    """折线图趋势响应。"""
    period_type: str
    category: str | None = Field(None, description="null 表示全部分类")
    data_points: list[TrendDataPoint]


class CategorySummary(BaseModel):
    """分类汇总。"""
    category: str
    category_label: str
    article_count: int
    total_read_count: int
    total_like_count: int
    total_share_count: int
    total_comment_count: int
    avg_read_count: int


class WechatStatsOverview(BaseModel):
    """微信统计概览。"""
    total_wechat_articles: int
    total_read_count: int
    total_interaction_count: int = Field(description="点赞+在看+分享+评论+收藏")
    category_summary: list[CategorySummary]
    top_articles: list[dict] = Field(
        default_factory=list,
        description="阅读量 Top 10 文章",
    )


class ArticleRankItem(BaseModel):
    """文章排名项。"""
    publish_record_id: int
    content_id: int
    title: str
    article_category: str
    read_count: int
    like_count: int
    share_count: int
    comment_count: int
    published_at: datetime | None
