from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.timezone import utc_now
from app.database import get_db
from app.models import User
from app.models.community import Community
from app.models.event import (
    ChecklistItem,
    Event,
    EventAttendee,
    EventPersonnel,
    EventTask,
    EventTemplate,
    FeedbackItem,
    IssueLink,
)
from app.schemas.event import (
    ChecklistItemCreate,
    ChecklistItemOut,
    ChecklistItemUpdate,
    EventCreate,
    EventOut,
    EventPersonnelCreate,
    EventPersonnelOut,
    EventStatusUpdate,
    EventTaskCreate,
    EventTaskOut,
    EventTaskUpdate,
    EventUpdate,
    FeedbackCreate,
    FeedbackOut,
    FeedbackStatusUpdate,
    IssueLinkCreate,
    IssueLinkOut,
    PaginatedEvents,
    PersonnelConfirmUpdate,
    TaskReorderRequest,
)

router = APIRouter()

VALID_EVENT_STATUSES = {"planning", "ongoing", "completed"}
VALID_EVENT_TYPES = {"online", "offline", "hybrid"}


# ─── Event CRUD ───────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedEvents)
def list_events(
    status: str | None = None,
    event_type: str | None = None,
    community_id: int | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Event)
    if community_id is not None:
        query = query.filter(Event.community_id == community_id)
    if status:
        query = query.filter(Event.status == status)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if keyword:
        query = query.filter(Event.title.ilike(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(Event.planned_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedEvents(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=EventOut, status_code=201)
def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(400, f"event_type 必须为 {VALID_EVENT_TYPES}")

    create_data = data.model_dump(exclude={"community_ids"})
    event = Event(
        owner_id=current_user.id,
        **create_data,
    )
    # 处理多对多社区关联
    all_ids = list(dict.fromkeys(data.community_ids + ([data.community_id] if data.community_id else [])))
    if all_ids:
        comms = db.query(Community).filter(Community.id.in_(all_ids)).all()
        event.communities = comms
        if not event.community_id and comms:
            event.community_id = comms[0].id
    db.add(event)
    db.flush()

    # 如果指定了模板，从模板复制 checklist
    if data.template_id:
        template = db.query(EventTemplate).filter(EventTemplate.id == data.template_id).first()
        if template:
            for titem in template.checklist_items:
                due = None
                if titem.deadline_offset_days is not None and event.planned_at:
                    due = (event.planned_at + timedelta(days=titem.deadline_offset_days)).date()
                db.add(ChecklistItem(
                    event_id=event.id,
                    phase=titem.phase,
                    title=titem.title,
                    description=titem.description,
                    is_mandatory=titem.is_mandatory,
                    responsible_role=titem.responsible_role,
                    reference_url=titem.reference_url,
                    due_date=due,
                    order=titem.order,
                ))

    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    return event


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    update_data = data.model_dump(exclude_unset=True, exclude={"community_ids"})
    for key, value in update_data.items():
        setattr(event, key, value)
    # 处理 community_ids 更新
    if data.community_ids is not None:
        comms = db.query(Community).filter(Community.id.in_(data.community_ids)).all()
        event.communities = comms
        event.community_id = comms[0].id if comms else None
    db.commit()
    db.refresh(event)
    return event


@router.patch("/{event_id}/status", response_model=EventOut)
def update_event_status(
    event_id: int,
    data: EventStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.status not in VALID_EVENT_STATUSES:
        raise HTTPException(400, f"status 必须为 {VALID_EVENT_STATUSES}")
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    event.status = data.status
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")
    db.delete(event)
    db.commit()


# ─── Checklist ────────────────────────────────────────────────────────────────

@router.get("/{event_id}/checklist", response_model=list[ChecklistItemOut])
def get_checklist(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    return sorted(event.checklist_items, key=lambda x: (x.phase, x.order))


@router.patch("/{event_id}/checklist/{item_id}", response_model=ChecklistItemOut)
def update_checklist_item(
    event_id: int,
    item_id: int,
    data: ChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(ChecklistItem).filter(
        ChecklistItem.id == item_id, ChecklistItem.event_id == event_id
    ).first()
    if not item:
        raise HTTPException(404, "检查项不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    if data.status == "done" and item.completed_at is None:
        item.completed_at = utc_now()
    elif data.status in ("pending", "skipped"):
        item.completed_at = None
    db.commit()
    db.refresh(item)
    return item


@router.post("/{event_id}/checklist", response_model=ChecklistItemOut, status_code=201)
def create_checklist_item(
    event_id: int,
    data: ChecklistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    item = ChecklistItem(event_id=event_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{event_id}/checklist/{item_id}", status_code=204)
def delete_checklist_item(
    event_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(ChecklistItem).filter(
        ChecklistItem.id == item_id, ChecklistItem.event_id == event_id
    ).first()
    if not item:
        raise HTTPException(404, "检查项不存在")
    db.delete(item)
    db.commit()


# ─── Personnel ────────────────────────────────────────────────────────────────

@router.get("/{event_id}/personnel", response_model=list[EventPersonnelOut])
def list_personnel(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    return sorted(event.personnel, key=lambda x: x.order)


@router.post("/{event_id}/personnel", response_model=EventPersonnelOut, status_code=201)
def add_personnel(
    event_id: int,
    data: EventPersonnelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    person = EventPersonnel(event_id=event_id, **data.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.patch("/{event_id}/personnel/{pid}/confirm", response_model=EventPersonnelOut)
def confirm_personnel(
    event_id: int,
    pid: int,
    data: PersonnelConfirmUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(EventPersonnel).filter(
        EventPersonnel.id == pid, EventPersonnel.event_id == event_id
    ).first()
    if not person:
        raise HTTPException(404, "人员记录不存在")
    person.confirmed = data.confirmed
    db.commit()
    db.refresh(person)
    return person


# ─── Attendees Import ─────────────────────────────────────────────────────────

@router.post("/{event_id}/attendees/import", status_code=200)
def import_attendees(
    event_id: int,
    rows: list[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量导入签到名单。每行需包含 person_id 字段（已确认匹配的 PersonProfile ID）。"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")

    created = 0
    skipped = 0
    for row in rows:
        person_id = row.get("person_id")
        if not person_id:
            skipped += 1
            continue
        existing = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.person_id == person_id,
        ).first()
        if existing:
            skipped += 1
            continue
        db.add(EventAttendee(
            event_id=event_id,
            person_id=person_id,
            checked_in=row.get("checked_in", False),
            role_at_event=row.get("role_at_event"),
            source="excel_import",
        ))
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped}


# ─── Feedback ─────────────────────────────────────────────────────────────────

@router.get("/{event_id}/feedback", response_model=list[FeedbackOut])
def list_feedback(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    return event.feedback_items


@router.post("/{event_id}/feedback", response_model=FeedbackOut, status_code=201)
def create_feedback(
    event_id: int,
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    feedback = FeedbackItem(event_id=event_id, **data.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.patch("/{event_id}/feedback/{fid}", response_model=FeedbackOut)
def update_feedback(
    event_id: int,
    fid: int,
    data: FeedbackStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedback = db.query(FeedbackItem).filter(
        FeedbackItem.id == fid, FeedbackItem.event_id == event_id
    ).first()
    if not feedback:
        raise HTTPException(404, "反馈记录不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(feedback, key, value)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.post("/{event_id}/feedback/{fid}/links", response_model=IssueLinkOut, status_code=201)
def link_issue(
    event_id: int,
    fid: int,
    data: IssueLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedback = db.query(FeedbackItem).filter(
        FeedbackItem.id == fid, FeedbackItem.event_id == event_id
    ).first()
    if not feedback:
        raise HTTPException(404, "反馈记录不存在")
    link = IssueLink(
        feedback_id=fid,
        linked_by_id=current_user.id,
        **data.model_dump(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


# ─── Event Tasks (甘特图) ──────────────────────────────────────────────────────

def _build_task_tree(tasks: list[EventTask]) -> list[EventTask]:
    """将平铺任务列表组装为父子树形结构（parent_task_id 分层）。"""
    task_map = {t.id: t for t in tasks}
    roots: list[EventTask] = []
    for task in tasks:
        task.children = []
    for task in tasks:
        if task.parent_task_id and task.parent_task_id in task_map:
            task_map[task.parent_task_id].children.append(task)
        else:
            roots.append(task)
    return roots


@router.get("/{event_id}/tasks", response_model=list[EventTaskOut])
def list_tasks(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    tasks = db.query(EventTask).filter(EventTask.event_id == event_id).order_by(EventTask.order).all()
    return _build_task_tree(tasks)


@router.post("/{event_id}/tasks", response_model=EventTaskOut, status_code=201)
def create_task(
    event_id: int,
    data: EventTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    task = EventTask(event_id=event_id, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    task.children = []
    return task


@router.patch("/{event_id}/tasks/{tid}", response_model=EventTaskOut)
def update_task(
    event_id: int,
    tid: int,
    data: EventTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(EventTask).filter(
        EventTask.id == tid, EventTask.event_id == event_id
    ).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    task.children = []
    return task


@router.delete("/{event_id}/tasks/{tid}", status_code=204)
def delete_task(
    event_id: int,
    tid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(EventTask).filter(
        EventTask.id == tid, EventTask.event_id == event_id
    ).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()


@router.patch("/{event_id}/tasks/reorder", status_code=200)
def reorder_tasks(
    event_id: int,
    data: TaskReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "活动不存在")
    for item in data.tasks:
        task = db.query(EventTask).filter(
            EventTask.id == item.task_id, EventTask.event_id == event_id
        ).first()
        if task:
            task.order = item.order
    db.commit()
    return {"ok": True}
