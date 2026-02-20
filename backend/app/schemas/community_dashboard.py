"""
社区工作台（Community Dashboard）Schemas

用于 GET /communities/{id}/dashboard 聚合 API 的请求/响应数据结构。
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


# ── 指标卡片 ──────────────────────────────────────────────────────────

class CommunityMetrics(BaseModel):
    """工作台 8 项核心指标"""
    # 内容指标
    total_contents: int = 0
    published_contents: int = 0
    pending_review_contents: int = 0
    draft_contents: int = 0
    # 治理指标
    committees_count: int = 0
    members_count: int = 0
    upcoming_meetings_count: int = 0
    active_channels_count: int = 0


# ── 趋势图 ──────────────────────────────────────────────────────────

class MonthlyTrend(BaseModel):
    """单月发布数据点"""
    month: str  # "2025-08" 格式
    count: int


class ChannelStats(BaseModel):
    """各渠道发布数量"""
    wechat: int = 0
    hugo: int = 0
    csdn: int = 0
    zhihu: int = 0


# ── 最近内容 ──────────────────────────────────────────────────────────

class RecentContentItem(BaseModel):
    """工作台内容列表项"""
    id: int
    title: str
    status: str          # draft / reviewing / approved / published
    work_status: str     # planning / in_progress / completed
    created_at: datetime
    owner_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── 即将召开的会议 ────────────────────────────────────────────────────

class UpcomingMeetingItem(BaseModel):
    """工作台会议列表项"""
    id: int
    title: str
    scheduled_at: datetime
    committee_name: str
    status: str          # scheduled / in_progress / completed / cancelled

    model_config = {"from_attributes": True}


# ── 日历事件 ────────────────────────────────────────────────────────

class CalendarEvent(BaseModel):
    """日历视图事件"""
    id: int
    type: str            # meeting / publish / member_join
    title: str
    date: datetime
    color: str           # 前端渲染色值
    resource_id: int     # 对应资源的 ID（会议 ID / 内容 ID / 用户 ID）
    resource_type: str   # 跳转时使用的路由类型


# ── 聚合响应 ────────────────────────────────────────────────────────

class CommunityDashboardResponse(BaseModel):
    """
    社区工作台完整聚合响应。
    前端通过单次请求获取工作台所需的全部数据。
    """
    community_id: int
    community_name: str
    community_logo: Optional[str] = None

    # 指标卡片
    metrics: CommunityMetrics

    # 趋势图：近 6 个月按月聚合
    publish_trend: List[MonthlyTrend] = []

    # 渠道统计
    channel_stats: ChannelStats = ChannelStats()

    # 工作队列
    recent_contents: List[RecentContentItem] = []
    upcoming_meetings: List[UpcomingMeetingItem] = []

    # 日历事件（近 30 天 + 未来 60 天）
    calendar_events: List[CalendarEvent] = []


# ── 超管社区总览 ────────────────────────────────────────────────────

class CommunityOverviewItem(BaseModel):
    """超管总览中单个社区的摘要信息"""
    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    is_active: bool
    members_count: int = 0
    contents_count: int = 0
    published_count: int = 0
    pending_review_count: int = 0
    committees_count: int = 0
    upcoming_meetings_count: int = 0
    active_channels_count: int = 0
    last_activity_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SuperuserOverviewResponse(BaseModel):
    """超管社区总览聚合响应（解决 N+1 查询）"""
    total_communities: int
    total_members: int
    total_contents: int
    communities: List[CommunityOverviewItem] = []
