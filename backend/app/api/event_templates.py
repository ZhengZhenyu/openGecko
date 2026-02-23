from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.models.event import ChecklistTemplateItem, EventTemplate
from app.schemas.event import EventTemplateCreate, EventTemplateListOut, EventTemplateOut, EventTemplateUpdate

router = APIRouter()


@router.get("", response_model=list[EventTemplateListOut])
def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(EventTemplate)
        .filter(EventTemplate.is_public == True)  # noqa: E712
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
    if not template.is_public:
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
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template
