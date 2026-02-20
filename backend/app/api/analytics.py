from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_community, get_current_user
from app.core.logging import get_logger
from app.database import get_db
from app.models import User
from app.models.content import Content
from app.models.publish_record import PublishRecord, ContentAnalytics
from app.schemas.publish import AnalyticsOut, AnalyticsOverview

router = APIRouter()
logger = get_logger(__name__)


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
            PublishRecord.status.in_(["published", "draft"]),
        )
        .group_by(PublishRecord.channel)
        .all()
    )
    channels = {ch: cnt for ch, cnt in channel_counts}

    return AnalyticsOverview(
        total_contents=total_contents,
        total_published=total_published,
        channels=channels,
    )


# ── Content analytics ─────────────────────────────────────────────────

@router.get("/{content_id}", response_model=list[AnalyticsOut])
def get_content_analytics(
    content_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """
    获取指定内容的发布分析数据。

    强制 community_id 过滤，确保只能查看当前社区的内容数据。
    """
    # 确保 content 属于当前社区，防止越权访问
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
        .all()
    )
    if not records:
        return []
    record_ids = [r.id for r in records]
    analytics = (
        db.query(ContentAnalytics)
        .filter(ContentAnalytics.publish_record_id.in_(record_ids))
        .order_by(ContentAnalytics.collected_at.desc())
        .all()
    )
    return analytics
