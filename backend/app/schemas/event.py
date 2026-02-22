from datetime import date, datetime

from pydantic import BaseModel

# ─── Event Template ───────────────────────────────────────────────────────────

class ChecklistTemplateItemCreate(BaseModel):
    phase: str  # pre / during / post
    title: str
    description: str | None = None
    order: int = 0


class ChecklistTemplateItemOut(BaseModel):
    id: int
    phase: str
    title: str
    description: str | None
    order: int

    model_config = {"from_attributes": True}


class EventTemplateCreate(BaseModel):
    name: str
    event_type: str  # online / offline / hybrid
    description: str | None = None
    is_public: bool = False
    checklist_items: list[ChecklistTemplateItemCreate] = []


class EventTemplateUpdate(BaseModel):
    name: str | None = None
    event_type: str | None = None
    description: str | None = None
    is_public: bool | None = None


class EventTemplateOut(BaseModel):
    id: int
    community_id: int
    name: str
    event_type: str
    description: str | None
    is_public: bool
    created_by_id: int | None
    created_at: datetime
    checklist_items: list[ChecklistTemplateItemOut] = []

    model_config = {"from_attributes": True}


class EventTemplateListOut(BaseModel):
    id: int
    name: str
    event_type: str
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Event ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title: str
    event_type: str = "offline"
    template_id: int | None = None
    planned_at: datetime | None = None
    duration_minutes: int | None = None
    location: str | None = None
    online_url: str | None = None
    description: str | None = None
    cover_image_url: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    planned_at: datetime | None = None
    duration_minutes: int | None = None
    location: str | None = None
    online_url: str | None = None
    description: str | None = None
    cover_image_url: str | None = None
    # 结果字段
    attendee_count: int | None = None
    online_count: int | None = None
    offline_count: int | None = None
    registration_count: int | None = None
    result_summary: str | None = None
    media_urls: list[str] | None = None


class EventStatusUpdate(BaseModel):
    status: str  # draft / planning / ongoing / completed / cancelled


class EventOut(BaseModel):
    id: int
    community_id: int
    title: str
    event_type: str
    template_id: int | None
    status: str
    planned_at: datetime | None
    duration_minutes: int | None
    location: str | None
    online_url: str | None
    description: str | None
    cover_image_url: str | None
    owner_id: int | None
    attendee_count: int | None
    online_count: int | None
    offline_count: int | None
    registration_count: int | None
    result_summary: str | None
    media_urls: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventListOut(BaseModel):
    id: int
    title: str
    event_type: str
    status: str
    planned_at: datetime | None
    location: str | None
    owner_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedEvents(BaseModel):
    items: list[EventListOut]
    total: int
    page: int
    page_size: int


# ─── Checklist Item ───────────────────────────────────────────────────────────

class ChecklistItemOut(BaseModel):
    id: int
    phase: str
    title: str
    status: str
    assignee_id: int | None
    due_date: date | None
    notes: str | None
    order: int

    model_config = {"from_attributes": True}


class ChecklistItemUpdate(BaseModel):
    status: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    notes: str | None = None


# ─── Event Personnel ──────────────────────────────────────────────────────────

class EventPersonnelCreate(BaseModel):
    role: str
    role_label: str | None = None
    assignee_type: str  # internal / external
    user_id: int | None = None
    person_id: int | None = None
    time_slot: str | None = None
    notes: str | None = None
    order: int = 0


class EventPersonnelOut(BaseModel):
    id: int
    role: str
    role_label: str | None
    assignee_type: str
    user_id: int | None
    person_id: int | None
    confirmed: str
    time_slot: str | None
    notes: str | None
    order: int

    model_config = {"from_attributes": True}


class PersonnelConfirmUpdate(BaseModel):
    confirmed: str  # pending / confirmed / declined


# ─── Feedback & Issue ─────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    content: str
    category: str = "question"
    raised_by: str | None = None
    raised_by_person_id: int | None = None
    assignee_id: int | None = None


class FeedbackStatusUpdate(BaseModel):
    status: str  # open / in_progress / closed
    assignee_id: int | None = None


class IssueLinkCreate(BaseModel):
    platform: str  # github / gitcode / gitee
    repo: str
    issue_number: int
    issue_url: str
    issue_type: str = "issue"
    issue_status: str = "open"


class IssueLinkOut(BaseModel):
    id: int
    platform: str
    repo: str
    issue_number: int
    issue_url: str
    issue_type: str
    issue_status: str
    linked_at: datetime
    linked_by_id: int | None

    model_config = {"from_attributes": True}


class FeedbackOut(BaseModel):
    id: int
    content: str
    category: str
    raised_by: str | None
    raised_by_person_id: int | None
    status: str
    assignee_id: int | None
    created_at: datetime
    issue_links: list[IssueLinkOut] = []

    model_config = {"from_attributes": True}


# ─── Event Task (甘特图) ──────────────────────────────────────────────────────

class EventTaskCreate(BaseModel):
    title: str
    task_type: str = "task"        # task / milestone
    phase: str = "pre"             # pre / during / post
    start_date: date | None = None
    end_date: date | None = None
    progress: int = 0
    status: str = "not_started"
    depends_on: list[int] = []
    parent_task_id: int | None = None
    order: int = 0


class EventTaskUpdate(BaseModel):
    title: str | None = None
    task_type: str | None = None
    phase: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    progress: int | None = None
    status: str | None = None
    depends_on: list[int] | None = None
    parent_task_id: int | None = None
    order: int | None = None


class EventTaskOut(BaseModel):
    id: int
    event_id: int
    title: str
    task_type: str
    phase: str
    start_date: date | None
    end_date: date | None
    progress: int
    status: str
    depends_on: list[int]
    parent_task_id: int | None
    order: int
    children: list["EventTaskOut"] = []

    model_config = {"from_attributes": True}


EventTaskOut.model_rebuild()


class TaskReorder(BaseModel):
    task_id: int
    order: int


class TaskReorderRequest(BaseModel):
    tasks: list[TaskReorder]
