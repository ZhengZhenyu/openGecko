from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import check_content_edit_permission, get_current_community, get_current_user
from app.database import get_db
from app.models import Content, User
from app.schemas.content import (
    ContentCalendarOut,
    ContentCreate,
    ContentOut,
    ContentScheduleUpdate,
    ContentStatusUpdate,
    ContentUpdate,
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
        work_status=data.work_status,
        community_id=community_id,
        created_by_user_id=current_user.id,
        owner_id=current_user.id,  # Creator is the initial owner
        scheduled_publish_at=data.scheduled_publish_at,
    )
    db.add(content)
    db.flush()  # Get content ID

    # Assign assignees (default to creator if empty) — batch query to avoid N+1
    assignee_ids = data.assignee_ids if data.assignee_ids else [current_user.id]
    assignee_users = db.query(User).filter(User.id.in_(assignee_ids)).all()
    for user in assignee_users:
        content.assignees.append(user)

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

    # Build response dict with assignee_ids
    content_dict = {
        **{c.name: getattr(content, c.name) for c in content.__table__.columns},
        "assignee_ids": [a.id for a in content.assignees]
    }
    return content_dict


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

    # Check edit permission
    if not check_content_edit_permission(content, current_user, db):
        raise HTTPException(403, "You don't have permission to edit this content")

    update_data = data.model_dump(exclude_unset=True)

    # Handle assignees update
    if "assignee_ids" in update_data:
        assignee_ids = update_data.pop("assignee_ids")
        content.assignees.clear()
        # Batch query to avoid N+1 when updating assignees
        if assignee_ids:
            assignee_users = db.query(User).filter(User.id.in_(assignee_ids)).all()
            for user in assignee_users:
                content.assignees.append(user)

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

    # Check edit permission
    if not check_content_edit_permission(content, current_user, db):
        raise HTTPException(403, "You don't have permission to delete this content")

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

    # Check edit permission
    if not check_content_edit_permission(content, current_user, db):
        raise HTTPException(403, "You don't have permission to update this content's status")

    content.status = data.status
    db.commit()
    db.refresh(content)
    return content


# Collaborators Management Endpoints

@router.get("/{content_id}/collaborators")
def list_collaborators(
    content_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List collaborators of a content.
    """
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
        for user in content.collaborators
    ]


@router.post("/{content_id}/collaborators/{user_id}", status_code=201)
def add_collaborator(
    content_id: int,
    user_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a collaborator to a content.
    Only the owner can add collaborators.
    """
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")

    # Only owner can add collaborators
    if content.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "Only the content owner can add collaborators")

    # Check if user exists and is a member of the community
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if not current_user.is_superuser and user not in content.community.members:
        raise HTTPException(400, "User is not a member of this community")

    # Check if already a collaborator
    if user in content.collaborators:
        raise HTTPException(400, "User is already a collaborator")

    content.collaborators.append(user)
    db.commit()

    return {"message": "Collaborator added successfully"}


@router.delete("/{content_id}/collaborators/{user_id}", status_code=204)
def remove_collaborator(
    content_id: int,
    user_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a collaborator from a content.
    Only the owner can remove collaborators.
    """
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")

    # Only owner can remove collaborators
    if content.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "Only the content owner can remove collaborators")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user not in content.collaborators:
        raise HTTPException(400, "User is not a collaborator")

    content.collaborators.remove(user)
    db.commit()


@router.put("/{content_id}/owner/{new_owner_id}", response_model=ContentOut)
def transfer_ownership(
    content_id: int,
    new_owner_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Transfer content ownership to another user.
    Only the current owner or superuser can transfer ownership.
    """
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")

    # Only owner or superuser can transfer ownership
    if content.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "Only the content owner can transfer ownership")

    # Check if new owner exists and is a member of the community
    new_owner = db.query(User).filter(User.id == new_owner_id).first()
    if not new_owner:
        raise HTTPException(404, "New owner not found")

    if not current_user.is_superuser and new_owner not in content.community.members:
        raise HTTPException(400, "New owner is not a member of this community")

    content.owner_id = new_owner_id
    db.commit()
    db.refresh(content)

    return content


# ==================== Calendar API Endpoints ====================


@router.get("/calendar/events", response_model=list[ContentCalendarOut])
def list_calendar_events(
    start: str = Query(..., description="Start date ISO format (e.g. 2026-02-01)"),
    end: str = Query(..., description="End date ISO format (e.g. 2026-03-01)"),
    status: str | None = None,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取日历视图的内容事件。
    返回指定日期范围内有 scheduled_publish_at 的内容，
    以及在该范围内创建但未设置发布时间的内容。
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use ISO format (e.g. 2026-02-01)") from None

    query = db.query(Content).filter(Content.community_id == community_id)

    if status:
        query = query.filter(Content.status == status)

    # Get contents that have a scheduled_publish_at in the date range
    # OR contents created in the date range (to show unscheduled items too)
    from sqlalchemy import and_, or_

    query = query.filter(
        or_(
            and_(
                Content.scheduled_publish_at.isnot(None),
                Content.scheduled_publish_at >= start_dt,
                Content.scheduled_publish_at < end_dt,
            ),
            and_(
                Content.scheduled_publish_at.is_(None),
                Content.created_at >= start_dt,
                Content.created_at < end_dt,
            ),
        )
    )

    items = query.order_by(Content.scheduled_publish_at.asc().nullslast()).all()
    return items


@router.patch("/{content_id}/schedule", response_model=ContentOut)
def update_content_schedule(
    content_id: int,
    data: ContentScheduleUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新内容的排期发布时间（用于日历拖拽）。
    """
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.community_id == community_id,
    ).first()
    if not content:
        raise HTTPException(404, "Content not found")

    # Check edit permission
    if not check_content_edit_permission(content, current_user, db):
        raise HTTPException(403, "You don't have permission to update this content's schedule")

    content.scheduled_publish_at = data.scheduled_publish_at
    db.commit()
    db.refresh(content)
    return content
