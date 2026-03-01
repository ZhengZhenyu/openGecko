from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_or_superuser, get_current_community, get_current_user
from app.core.logging import get_logger
from app.database import get_db
from app.models import User
from app.models.channel import ChannelConfig
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.schemas.publish import AnalyticsOverview, ChannelConfigOut, ChannelConfigUpdate, ContentAnalyticsDetail

router = APIRouter()
logger = get_logger(__name__)

SUPPORTED_CHANNELS = {"wechat", "hugo", "csdn", "zhihu"}
SENSITIVE_FIELDS = {"app_secret", "cookie", "token", "secret", "password", "api_key"}


# ── Overview ──────────────────────────────────────────────────────────

@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """
    获取当前社区的内容发布分析概览。

    修复多租户安全漏洞：强制通过 X-Community-Id 过滤，防止跨社区数据泄露。
    """
    total_contents = (
        db.query(Content)
        .filter(Content.community_id == community_id)
        .count()
    )
    total_published = (
        db.query(PublishRecord)
        .filter(
            PublishRecord.community_id == community_id,
            PublishRecord.status == "published",
        )
        .count()
    )

    channel_counts = (
        db.query(PublishRecord.channel, func.count(PublishRecord.id))
        .filter(
            PublishRecord.community_id == community_id,
            PublishRecord.status == "published",
        )
        .group_by(PublishRecord.channel)
        .all()
    )
    channels = dict(channel_counts)

    return AnalyticsOverview(
        total_contents=total_contents,
        total_published=total_published,
        channels=channels,
    )


# ── Channel Settings ──────────────────────────────────────────────────
# 注意：这些路由必须在 /{content_id} 之前注册，避免被通配路由拦截。

def _mask_sensitive_config(config: dict) -> dict:
    """将敏感字段值脱敏后返回。"""
    masked = {}
    for k, v in config.items():
        if any(sf in k.lower() for sf in SENSITIVE_FIELDS) and v:
            masked[k] = "••••••" + str(v)[-4:] if len(str(v)) > 4 else "••••"
        else:
            masked[k] = v
    return masked


@router.get("/settings/channels", response_model=list[ChannelConfigOut])
def get_channel_settings(
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前社区所有渠道配置（含默认渠道）。
    返回 wechat/hugo/csdn/zhihu 的配置状态，未配置的渠道返回默认值。
    """
    existing = {
        cfg.channel: cfg
        for cfg in db.query(ChannelConfig)
        .filter(ChannelConfig.community_id == community_id)
        .all()
    }

    result = []
    for channel in sorted(SUPPORTED_CHANNELS):
        if channel in existing:
            cfg = existing[channel]
            masked_config = _mask_sensitive_config(cfg.config) if cfg.config else {}
            result.append(ChannelConfigOut(
                id=cfg.id,
                channel=cfg.channel,
                config=masked_config,
                enabled=cfg.enabled,
            ))
        else:
            result.append(ChannelConfigOut(
                id=-1,
                channel=channel,
                config={},
                enabled=False,
            ))
    return result


@router.put("/settings/channels/{channel}", response_model=ChannelConfigOut)
def update_channel_settings(
    channel: str,
    data: ChannelConfigUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_admin_or_superuser),
    db: Session = Depends(get_db),
):
    """
    创建或更新指定渠道的配置（upsert）。需要社区管理员权限。
    """
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的渠道类型。可选: {', '.join(sorted(SUPPORTED_CHANNELS))}",
        )

    existing = (
        db.query(ChannelConfig)
        .filter(
            ChannelConfig.community_id == community_id,
            ChannelConfig.channel == channel,
        )
        .first()
    )

    if existing:
        if data.config:
            existing.config = data.config
        if data.enabled is not None:
            existing.enabled = data.enabled
        db.commit()
        db.refresh(existing)
        cfg = existing
    else:
        cfg = ChannelConfig(
            community_id=community_id,
            channel=channel,
            config=data.config or {},
            enabled=data.enabled if data.enabled is not None else False,
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    masked_config = _mask_sensitive_config(cfg.config) if cfg.config else {}
    return ChannelConfigOut(
        id=cfg.id,
        channel=cfg.channel,
        config=masked_config,
        enabled=cfg.enabled,
    )


# ── Publish trend ──────────────────────────────────────────────────────
# 注意：所有具名路由必须在通配路由 /{content_id} 之前注册

@router.get("/trend/daily")
def get_publish_trend(
    days: int = 30,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """
    获取最近 N 天内每天的发布数量（仅统计 published 状态），用于趋势折线图。
    """
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(PublishRecord.published_at).label("date"),
            func.count(PublishRecord.id).label("count"),
        )
        .filter(
            PublishRecord.community_id == community_id,
            PublishRecord.status == "published",
            PublishRecord.published_at >= since,
        )
        .group_by(func.date(PublishRecord.published_at))
        .order_by(func.date(PublishRecord.published_at))
        .all()
    )
    # 补齐所有日期（没有发布的天为 0）
    date_map: dict[str, int] = {str(r.date): r.count for r in rows}
    result = []
    for i in range(days):
        day = (since + timedelta(days=i + 1)).date()
        result.append({"date": str(day), "count": date_map.get(str(day), 0)})
    return {"items": result, "days": days}


# ── Content analytics ─────────────────────────────────────────────────
# 通配路由 /{content_id} 必须在所有具体路由之后注册

@router.get("/{content_id}", response_model=ContentAnalyticsDetail)
def get_content_analytics(
    content_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """
    获取指定内容的发布分析数据（含发布渠道统计）。
    强制 community_id 过滤，确保只能查看当前社区的内容数据。
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id, Content.community_id == community_id)
        .first()
    )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在或无权访问",
        )

    records = (
        db.query(PublishRecord)
        .filter(
            PublishRecord.content_id == content_id,
            PublishRecord.community_id == community_id,
        )
        .order_by(PublishRecord.published_at.desc())
        .all()
    )
    return ContentAnalyticsDetail(content_id=content.id, title=content.title, analytics=records)
