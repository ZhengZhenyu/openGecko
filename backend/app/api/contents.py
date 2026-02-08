from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_current_community
from app.database import get_db
from app.models import User, Content
from app.schemas.content import (
    ContentCreate,
    ContentOut,
    ContentUpdate,
    ContentStatusUpdate,
    ContentListOut,
    PaginatedContents,
)
from app.services.converter import convert_markdown_to_html

router = APIRouter()

VALID_STATUSES = {"draft", "reviewing", "approved", "published"}
VALID_SOURCE_TYPES = {"contribution", "release_note", "event_summary"}


@router.get("", response_model=PaginatedContents)
def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    source_type: str | None = None,
    keyword: str | None = None,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Filter by community
    query = db.query(Content).filter(Content.community_id == community_id)

    if status:
        query = query.filter(Content.status == status)
    if source_type:
        query = query.filter(Content.source_type == source_type)
    if keyword:
        query = query.filter(Content.title.contains(keyword))
    total = query.count()
    items = query.order_by(Content.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedContents(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ContentOut, status_code=201)
def create_content(
    data: ContentCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(400, f"Invalid source_type, must be one of {VALID_SOURCE_TYPES}")
    content_html = convert_markdown_to_html(data.content_markdown) if data.content_markdown else ""
    content = Content(
        title=data.title,
        content_markdown=data.content_markdown,
        content_html=content_html,
        source_type=data.source_type,
        author=data.author,
        tags=data.tags,
        category=data.category,
        cover_image=data.cover_image,
        status="draft",
        community_id=community_id,
        created_by_user_id=current_user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


@router.get("/{content_id}", response_model=ContentOut)
def get_content(
    content_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")
    return content


@router.put("/{content_id}", response_model=ContentOut)
def update_content(
    content_id: int,
    data: ContentUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")
    update_data = data.model_dump(exclude_unset=True)
    if "content_markdown" in update_data:
        update_data["content_html"] = convert_markdown_to_html(update_data["content_markdown"])
    for key, value in update_data.items():
        setattr(content, key, value)
    db.commit()
    db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=204)
def delete_content(
    content_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")
    db.delete(content)
    db.commit()


@router.patch("/{content_id}/status", response_model=ContentOut)
def update_content_status(
    content_id: int,
    data: ContentStatusUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status, must be one of {VALID_STATUSES}")
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")
    content.status = data.status
    db.commit()
    db.refresh(content)
    return content
