import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_community
from app.core.timezone import utc_now
from app.database import get_db
from app.models.content import Content
from app.models.publish_record import PublishRecord
from app.schemas.publish import (
    ChannelPreview,
    CopyContent,
    PublishRecordListOut,
    PublishRecordOut,
    PublishRequest,
)
from app.services.csdn import csdn_service
from app.services.hugo import hugo_service
from app.services.wechat import wechat_service
from app.services.zhihu import zhihu_service

router = APIRouter()


def _get_content_or_404(content_id: int, db: Session) -> Content:
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(404, "Content not found")
    return content


# ── Publish to WeChat (create draft) ──────────────────────────────────

@router.post("/{content_id}/wechat", response_model=PublishRecordOut, status_code=201)
async def publish_to_wechat(
    content_id: int,
    data: PublishRequest | None = None,
    db: Session = Depends(get_db),
):
    content = _get_content_or_404(content_id, db)
    community_id = content.community_id

    # 优先使用 content_html（如 135 编辑器导入的 HTML），否则从 Markdown 转换
    if content.content_html and content.content_html.strip():
        wechat_html = wechat_service.apply_wechat_styles(content.content_html)
    else:
        # Replace local images with WeChat URLs before conversion
        markdown_with_wechat_images = await wechat_service._replace_local_images_with_wechat_urls(
            content.content_markdown, community_id
        )
        wechat_html = wechat_service.convert_to_wechat_html(markdown_with_wechat_images)

    # Resolve thumb_media_id: explicit param > auto-upload cover_image
    thumb_media_id = data.thumb_media_id if data and data.thumb_media_id else ""
    if not thumb_media_id and content.cover_image:
        cover_path = os.path.join(settings.UPLOAD_DIR, content.cover_image.removeprefix("/uploads/"))
        if os.path.isfile(cover_path):
            try:
                thumb_media_id = await wechat_service.upload_thumb_media(cover_path, community_id)
            except Exception as e:
                raise HTTPException(502, f"封面图上传失败: {e}") from e
    if not thumb_media_id:
        raise HTTPException(
            400,
            "缺少封面图。请在内容编辑页设置封面图（cover_image），或在请求中提供 thumb_media_id",
        )

    try:
        result = await wechat_service.create_draft(
            title=content.title,
            content_html=wechat_html,
            author=content.author,
            thumb_media_id=thumb_media_id,
            community_id=community_id,
        )
    except ValueError as e:
        # Configuration errors (missing credentials)
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        record = PublishRecord(
            content_id=content_id,
            channel="wechat",
            status="failed",
            error_message=str(e),
            community_id=community_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        raise HTTPException(502, f"WeChat API error: {e}") from e

    record = PublishRecord(
        content_id=content_id,
        channel="wechat",
        status="draft",
        platform_article_id=result.get("media_id", ""),
        community_id=community_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ── Publish to Hugo ───────────────────────────────────────────────────

@router.post("/{content_id}/hugo", response_model=PublishRecordOut, status_code=201)
def publish_to_hugo(content_id: int, db: Session = Depends(get_db)):
    content = _get_content_or_404(content_id, db)
    community_id = content.community_id

    try:
        file_path = hugo_service.save_post(
            title=content.title,
            markdown_content=content.content_markdown,
            author=content.author,
            tags=content.tags,
            category=content.category,
            community_id=community_id,
        )
    except ValueError as e:
        # Configuration errors (missing repo path)
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        record = PublishRecord(
            content_id=content_id,
            channel="hugo",
            status="failed",
            error_message=str(e),
            community_id=community_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        raise HTTPException(500, f"Hugo publish error: {e}") from e

    record = PublishRecord(
        content_id=content_id,
        channel="hugo",
        status="published",
        platform_url=file_path,
        published_at=utc_now(),
        community_id=community_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ── Preview for any channel ───────────────────────────────────────────

@router.get("/{content_id}/preview/{channel}", response_model=ChannelPreview)
def preview_for_channel(content_id: int, channel: str, db: Session = Depends(get_db)):
    content = _get_content_or_404(content_id, db)

    if channel == "wechat":
        html = wechat_service.convert_to_wechat_html(content.content_markdown)
        return ChannelPreview(channel="wechat", title=content.title, content=html, format="html")
    elif channel == "hugo":
        md = hugo_service.preview_post(
            content.title, content.content_markdown, content.author, content.tags, content.category
        )
        return ChannelPreview(channel="hugo", title=content.title, content=md, format="markdown")
    elif channel == "csdn":
        result = csdn_service.format_for_csdn(
            content.title, content.content_markdown, content.tags, content.category
        )
        return ChannelPreview(channel="csdn", title=content.title, content=result["content"], format="markdown")
    elif channel == "zhihu":
        result = zhihu_service.format_for_zhihu(content.title, content.content_markdown)
        return ChannelPreview(channel="zhihu", title=content.title, content=result["html"], format="html")
    else:
        raise HTTPException(400, f"Unknown channel: {channel}")


# ── Copy content for CSDN / Zhihu ────────────────────────────────────

@router.get("/{content_id}/copy/{channel}", response_model=CopyContent)
def get_copy_content(content_id: int, channel: str, db: Session = Depends(get_db)):
    content = _get_content_or_404(content_id, db)

    if channel == "csdn":
        result = csdn_service.format_for_csdn(
            content.title, content.content_markdown, content.tags, content.category
        )
        return CopyContent(channel="csdn", **result)
    elif channel == "zhihu":
        result = zhihu_service.format_for_zhihu(content.title, content.content_markdown)
        return CopyContent(
            channel="zhihu",
            title=result["title"],
            content=result["markdown"],
            format="markdown",
            platform="zhihu",
        )
    else:
        raise HTTPException(400, f"Copy not supported for channel: {channel}. Use publish endpoint instead.")


# ── Publish records ───────────────────────────────────────────────────

@router.get("/records", response_model=PublishRecordListOut)
def list_publish_records(
    content_id: int | None = None,
    channel: str | None = None,
    db: Session = Depends(get_db),
    community_id: int = Depends(get_current_community)
):
    # Multi-tenant filtering: only show records from current community
    query = db.query(PublishRecord).filter(
        PublishRecord.community_id == community_id
    ).order_by(PublishRecord.created_at.desc())

    if content_id:
        query = query.filter(PublishRecord.content_id == content_id)
    if channel:
        query = query.filter(PublishRecord.channel == channel)

    items = query.limit(100).all()
    total = query.count()

    return PublishRecordListOut(total=total, items=items)
