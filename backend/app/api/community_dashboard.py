"""
社区工作台聚合 API

提供单一端点 GET /communities/{id}/dashboard，
聚合返回工作台所需的全部数据，避免前端多次请求（N+1 问题）。

权限：社区成员（admin / user）均可访问，Superuser 可访问任意社区。
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user, get_current_community, get_user_community_role
from app.core.logging import get_logger
from app.database import get_db
from app.models import User, Community
from app.models.channel import ChannelConfig
from app.models.committee import Committee
from app.models.content import Content
from app.models.meeting import Meeting
from app.models.publish_record import PublishRecord
from app.models.user import community_users
from app.schemas.community_dashboard import (
    CalendarEvent,
    ChannelStats,
    CommunityDashboardResponse,
    CommunityMetrics,
    CommunityOverviewItem,
    MonthlyTrend,
    RecentContentItem,
    SuperuserOverviewResponse,
    UpcomingMeetingItem,
)

router = APIRouter()
logger = get_logger(__name__)


# ── 社区工作台 ────────────────────────────────────────────────────────

@router.get("/{community_id}/dashboard", response_model=CommunityDashboardResponse)
def get_community_dashboard(
    community_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取社区工作台聚合数据。

    单次 API 请求返回以下数据：
    - 8 项核心指标卡片
    - 近 6 个月内容发布趋势（折线图）
    - 各渠道发布统计（条形图）
    - 最近 5 条内容
    - 即将召开的 5 场会议
    - 日历事件（近 30 天 + 未来 60 天）

    权限：社区成员（admin / user）均可访问。
    """
    # 权限校验：验证用户有权访问该社区
    if not current_user.is_superuser:
        role = get_user_community_role(current_user, community_id, db)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该社区",
            )

    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="社区不存在",
        )

    now = datetime.utcnow()

    # ── 1. 指标卡片聚合（单批查询）──────────────────────────────────────

    # 内容指标（4 个）—— 用分开的 count 查询，兼容 SQLite 和 PostgreSQL
    total_contents = db.query(Content).filter(Content.community_id == community_id).count()
    published_contents = (
        db.query(Content)
        .filter(Content.community_id == community_id, Content.status == "published")
        .count()
    )
    pending_review_contents = (
        db.query(Content)
        .filter(Content.community_id == community_id, Content.status == "reviewing")
        .count()
    )
    draft_contents = (
        db.query(Content)
        .filter(Content.community_id == community_id, Content.status == "draft")
        .count()
    )

    # 治理指标（4 个）
    committees_count = (
        db.query(Committee)
        .filter(Committee.community_id == community_id)
        .count()
    )

    members_count = db.execute(
        select(func.count()).select_from(community_users).where(
            community_users.c.community_id == community_id
        )
    ).scalar() or 0

    upcoming_meetings_count = (
        db.query(Meeting)
        .filter(
            Meeting.community_id == community_id,
            Meeting.scheduled_at >= now,
            Meeting.status == "scheduled",
        )
        .count()
    )

    active_channels_count = (
        db.query(ChannelConfig)
        .filter(
            ChannelConfig.community_id == community_id,
            ChannelConfig.enabled == True,  # noqa: E712
        )
        .count()
    )

    metrics = CommunityMetrics(
        total_contents=total_contents,
        published_contents=published_contents,
        pending_review_contents=pending_review_contents,
        draft_contents=draft_contents,
        committees_count=committees_count,
        members_count=members_count,
        upcoming_meetings_count=upcoming_meetings_count,
        active_channels_count=active_channels_count,
    )

    # ── 2. 发布趋势（近 6 个月）──────────────────────────────────────────

    six_months_ago = now - timedelta(days=180)

    # 查询近 6 个月已发布的记录
    published_records = (
        db.query(
            PublishRecord.published_at,
        )
        .filter(
            PublishRecord.community_id == community_id,
            PublishRecord.status == "published",
            PublishRecord.published_at >= six_months_ago,
        )
        .all()
    )

    # 按年月聚合
    month_counts: dict[str, int] = {}
    for (published_at,) in published_records:
        if published_at:
            month_key = published_at.strftime("%Y-%m")
            month_counts[month_key] = month_counts.get(month_key, 0) + 1

    # 生成连续 6 个月的趋势数据（补零）
    publish_trend = []
    for i in range(5, -1, -1):
        dt = now - timedelta(days=30 * i)
        month_key = dt.strftime("%Y-%m")
        publish_trend.append(
            MonthlyTrend(month=month_key, count=month_counts.get(month_key, 0))
        )

    # ── 3. 渠道发布统计 ────────────────────────────────────────────────

    channel_rows = (
        db.query(PublishRecord.channel, func.count(PublishRecord.id))
        .filter(
            PublishRecord.community_id == community_id,
            PublishRecord.status == "published",
        )
        .group_by(PublishRecord.channel)
        .all()
    )
    ch_dict = {ch: cnt for ch, cnt in channel_rows}
    channel_stats = ChannelStats(
        wechat=ch_dict.get("wechat", 0),
        hugo=ch_dict.get("hugo", 0),
        csdn=ch_dict.get("csdn", 0),
        zhihu=ch_dict.get("zhihu", 0),
    )

    # ── 4. 最近 5 条内容 ───────────────────────────────────────────────

    recent_raw = (
        db.query(Content)
        .filter(Content.community_id == community_id)
        .order_by(Content.created_at.desc())
        .limit(5)
        .all()
    )
    # 预取 owner 用户名
    recent_contents = []
    for c in recent_raw:
        owner_name = None
        if c.owner_id:
            owner = db.query(User).filter(User.id == c.owner_id).first()
            owner_name = owner.full_name or owner.username if owner else None
        recent_contents.append(
            RecentContentItem(
                id=c.id,
                title=c.title,
                status=c.status,
                work_status=c.work_status or "planning",
                created_at=c.created_at,
                owner_name=owner_name,
            )
        )

    # ── 5. 即将召开的 5 场会议 ────────────────────────────────────────

    upcoming_raw = (
        db.query(Meeting)
        .options(joinedload(Meeting.committee))
        .filter(
            Meeting.community_id == community_id,
            Meeting.scheduled_at >= now,
            Meeting.status == "scheduled",
        )
        .order_by(Meeting.scheduled_at.asc())
        .limit(5)
        .all()
    )
    upcoming_meetings = [
        UpcomingMeetingItem(
            id=m.id,
            title=m.title,
            scheduled_at=m.scheduled_at,
            committee_name=m.committee.name if m.committee else "未知委员会",
            status=m.status,
        )
        for m in upcoming_raw
    ]

    # ── 6. 日历事件（近 30 天 + 未来 60 天）──────────────────────────

    cal_start = now - timedelta(days=30)
    cal_end = now + timedelta(days=60)
    calendar_events: list[CalendarEvent] = []

    # 会议事件（蓝色 #0095ff）
    meeting_events = (
        db.query(Meeting)
        .options(joinedload(Meeting.committee))
        .filter(
            Meeting.community_id == community_id,
            Meeting.scheduled_at >= cal_start,
            Meeting.scheduled_at <= cal_end,
        )
        .all()
    )
    for m in meeting_events:
        committee_name = m.committee.name if m.committee else ""
        calendar_events.append(
            CalendarEvent(
                id=m.id,
                type="meeting",
                title=f"{m.title}" + (f" ({committee_name})" if committee_name else ""),
                date=m.scheduled_at,
                color="#0095ff",
                resource_id=m.id,
                resource_type="meeting",
            )
        )

    # 内容发布事件（绿色 #10b981）
    publish_events = (
        db.query(PublishRecord)
        .filter(
            PublishRecord.community_id == community_id,
            PublishRecord.status == "published",
            PublishRecord.published_at >= cal_start,
            PublishRecord.published_at <= cal_end,
        )
        .all()
    )
    seen_content_ids = set()
    for pr in publish_events:
        if pr.content_id not in seen_content_ids:
            seen_content_ids.add(pr.content_id)
            content = db.query(Content).filter(Content.id == pr.content_id).first()
            if content:
                calendar_events.append(
                    CalendarEvent(
                        id=pr.id,
                        type="publish",
                        title=content.title,
                        date=pr.published_at,
                        color="#10b981",
                        resource_id=pr.content_id,
                        resource_type="content",
                    )
                )

    # 成员加入事件（橙色 #f59e0b）
    member_join_rows = db.execute(
        select(
            community_users.c.user_id,
            community_users.c.joined_at,
        ).where(
            community_users.c.community_id == community_id,
            community_users.c.joined_at >= cal_start,
            community_users.c.joined_at <= cal_end,
        )
    ).all()
    for user_id, joined_at in member_join_rows:
        if joined_at:
            member = db.query(User).filter(User.id == user_id).first()
            if member:
                display_name = member.full_name or member.username
                calendar_events.append(
                    CalendarEvent(
                        id=user_id,
                        type="member_join",
                        title=f"{display_name} 加入社区",
                        date=joined_at,
                        color="#f59e0b",
                        resource_id=user_id,
                        resource_type="user",
                    )
                )

    # 按日期排序
    calendar_events.sort(key=lambda e: e.date)

    logger.info(
        "工作台数据加载完成",
        extra={
            "community_id": community_id,
            "contents": total_contents,
            "meetings": upcoming_meetings_count,
            "events": len(calendar_events),
        },
    )

    return CommunityDashboardResponse(
        community_id=community_id,
        community_name=community.name,
        community_logo=community.logo_url,
        metrics=metrics,
        publish_trend=publish_trend,
        channel_stats=channel_stats,
        recent_contents=recent_contents,
        upcoming_meetings=upcoming_meetings,
        calendar_events=calendar_events,
    )


# ── 超管社区总览 ────────────────────────────────────────────────────

@router.get("/overview/stats", response_model=SuperuserOverviewResponse)
def get_superuser_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取平台所有社区的汇总统计（仅超级管理员可用）。

    解决 N+1 查询问题：使用聚合 SQL 一次性返回所有社区统计，
    而非对每个社区逐一发起请求。
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅平台超级管理员可访问",
        )

    now = datetime.utcnow()
    communities = db.query(Community).order_by(Community.created_at.desc()).all()

    # 批量查询各社区统计（避免 N+1）
    # 成员数
    member_counts = dict(
        db.execute(
            select(
                community_users.c.community_id,
                func.count(community_users.c.user_id).label("cnt"),
            ).group_by(community_users.c.community_id)
        ).all()
    )

    # 内容数 & 已发布数 & 待审核数
    content_rows = db.execute(
        select(
            Content.community_id,
            func.count(Content.id).label("total"),
            func.sum(
                case((Content.status == "published", 1), else_=0)
            ).label("published"),
            func.sum(
                case((Content.status == "reviewing", 1), else_=0)
            ).label("reviewing"),
        ).group_by(Content.community_id)
    ).all()
    content_stats_map = {
        row.community_id: {
            "total": row.total or 0,
            "published": row.published or 0,
            "reviewing": row.reviewing or 0,
        }
        for row in content_rows
    }

    # 委员会数
    committee_counts = dict(
        db.execute(
            select(
                Committee.community_id,
                func.count(Committee.id).label("cnt"),
            ).group_by(Committee.community_id)
        ).all()
    )

    # 即将召开会议数
    upcoming_meeting_counts = dict(
        db.execute(
            select(
                Meeting.community_id,
                func.count(Meeting.id).label("cnt"),
            ).where(
                Meeting.scheduled_at >= now,
                Meeting.status == "scheduled",
            ).group_by(Meeting.community_id)
        ).all()
    )

    # 活跃渠道数
    channel_counts = dict(
        db.execute(
            select(
                ChannelConfig.community_id,
                func.count(ChannelConfig.id).label("cnt"),
            ).where(
                ChannelConfig.enabled == True  # noqa: E712
            ).group_by(ChannelConfig.community_id)
        ).all()
    )

    # 最近活动时间（最新内容的 created_at）
    latest_content_rows = db.execute(
        select(
            Content.community_id,
            func.max(Content.created_at).label("latest"),
        ).group_by(Content.community_id)
    ).all()
    latest_activity_map = {row.community_id: row.latest for row in latest_content_rows}

    # 组装响应
    overview_items = []
    for community in communities:
        cid = community.id
        cs = content_stats_map.get(cid, {"total": 0, "published": 0, "reviewing": 0})
        overview_items.append(
            CommunityOverviewItem(
                id=cid,
                name=community.name,
                slug=community.slug,
                logo_url=community.logo_url,
                is_active=community.is_active,
                members_count=member_counts.get(cid, 0),
                contents_count=cs["total"],
                published_count=cs["published"],
                pending_review_count=cs["reviewing"],
                committees_count=committee_counts.get(cid, 0),
                upcoming_meetings_count=upcoming_meeting_counts.get(cid, 0),
                active_channels_count=channel_counts.get(cid, 0),
                last_activity_at=latest_activity_map.get(cid),
            )
        )

    total_members = sum(member_counts.values()) if member_counts else 0
    total_contents = sum(cs["total"] for cs in content_stats_map.values())

    return SuperuserOverviewResponse(
        total_communities=len(communities),
        total_members=total_members,
        total_contents=total_contents,
        communities=overview_items,
    )
