from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.models.event import ChecklistTemplateItem, EventTemplate
from app.schemas.event import (
    ChecklistTemplateItemCreate,
    ChecklistTemplateItemOut,
    ChecklistTemplateItemUpdate,
    EventTemplateCreate,
    EventTemplateListOut,
    EventTemplateOut,
    EventTemplateUpdate,
)

router = APIRouter()


@router.get("", response_model=list[EventTemplateListOut])
def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(EventTemplate)
        .filter(
            or_(
                EventTemplate.is_public == True,  # noqa: E712
                EventTemplate.created_by_id == current_user.id,
            )
        )
        .order_by(EventTemplate.created_at.desc())
        .all()
    )


@router.post("", response_model=EventTemplateOut, status_code=201)
def create_template(
    data: EventTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = EventTemplate(
        community_id=None,
        name=data.name,
        event_type=data.event_type,
        description=data.description,
        is_public=data.is_public,
        created_by_id=current_user.id,
    )
    db.add(template)
    db.flush()

    for item_data in data.checklist_items:
        item = ChecklistTemplateItem(template_id=template.id, **item_data.model_dump())
        db.add(item)

    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=EventTemplateOut)
def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if not template.is_public and template.created_by_id != current_user.id:
        raise HTTPException(403, "无权访问此模板")
    return template


@router.patch("/{template_id}", response_model=EventTemplateOut)
def update_template(
    template_id: int,
    data: EventTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "无权修改此模板")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "无权删除此模板")
    db.delete(template)
    db.commit()


# ─── Template Checklist Item CRUD ─────────────────────────────────────────────

@router.post("/{template_id}/items", response_model=ChecklistTemplateItemOut, status_code=201)
def add_template_item(
    template_id: int,
    data: ChecklistTemplateItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "无权修改此模板")
    item = ChecklistTemplateItem(template_id=template_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{template_id}/items/{item_id}", response_model=ChecklistTemplateItemOut)
def update_template_item(
    template_id: int,
    item_id: int,
    data: ChecklistTemplateItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "无权修改此模板")
    item = db.query(ChecklistTemplateItem).filter(
        ChecklistTemplateItem.id == item_id,
        ChecklistTemplateItem.template_id == template_id,
    ).first()
    if not item:
        raise HTTPException(404, "条目不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{template_id}/items/{item_id}", status_code=204)
def delete_template_item(
    template_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(EventTemplate).filter(EventTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if template.created_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "无权修改此模板")
    item = db.query(ChecklistTemplateItem).filter(
        ChecklistTemplateItem.id == item_id,
        ChecklistTemplateItem.template_id == template_id,
    ).first()
    if not item:
        raise HTTPException(404, "条目不存在")
    db.delete(item)
    db.commit()
