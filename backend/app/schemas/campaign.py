from datetime import date, datetime

from pydantic import BaseModel

# ─── Campaign ─────────────────────────────────────────────────────────────────
# 活动类型说明：
#   default          — 默认活动（日常工作量/时间记录，节日海报推送等）
#   community_care   — 社区成员关怀（委员会委员等，支持从委员会导入、Excel导入）
#   developer_care   — 开发者关怀（面向大量人群，支持Excel批量导入）
#   promotion        — 推广宣传（旧版，保留兼容）
#   care             — 关怀回访（旧版，保留兼容）
#   invitation       — 邀请加入（旧版，保留兼容）
#   survey           — 问卷调研（旧版，保留兼容）

class CampaignCreate(BaseModel):
    name: str
    type: str  # default / community_care / developer_care / promotion / care / invitation / survey
    community_id: int | None = None
    description: str | None = None
    owner_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    status: str | None = None   # draft / active / completed / archived
    owner_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class CampaignListOut(BaseModel):
    id: int
    community_id: int | None
    name: str
    type: str
    status: str
    start_date: date | None
    end_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignOut(CampaignListOut):
    description: str | None
    owner_id: int | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Campaign Contact ──────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    person_id: int
    channel: str | None = None
    notes: str | None = None
    assigned_to_id: int | None = None


class ContactStatusUpdate(BaseModel):
    status: str          # pending/contacted/responded/converted/declined
    channel: str | None = None
    notes: str | None = None
    assigned_to_id: int | None = None


class PersonSnapshot(BaseModel):
    id: int
    display_name: str
    company: str | None
    email: str | None
    github_handle: str | None

    model_config = {"from_attributes": True}


class ContactOut(BaseModel):
    id: int
    campaign_id: int
    person_id: int
    status: str
    channel: str | None
    added_by: str
    last_contacted_at: datetime | None
    notes: str | None
    assigned_to_id: int | None
    person: PersonSnapshot | None = None

    model_config = {"from_attributes": True}


class PaginatedContacts(BaseModel):
    items: list[ContactOut]
    total: int
    page: int
    page_size: int


# ─── Campaign Activity ─────────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    action: str   # sent_email/made_call/sent_wechat/in_person_meeting/got_reply/note
    content: str | None = None
    outcome: str | None = None


class ActivityOut(BaseModel):
    id: int
    campaign_id: int
    person_id: int
    action: str
    content: str | None
    outcome: str | None
    operator_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Funnel / Stats ───────────────────────────────────────────────────────────

class CampaignFunnel(BaseModel):
    pending: int = 0
    contacted: int = 0
    total: int = 0


# ─── Bulk Import ──────────────────────────────────────────────────────────────

class BulkImportFromEvent(BaseModel):
    event_id: int
    channel: str | None = None
    assigned_to_id: int | None = None


class BulkImportFromPeople(BaseModel):
    person_ids: list[int]
    channel: str | None = None
    assigned_to_id: int | None = None


# ─── Committee Import ─────────────────────────────────────────────────────────

class CommitteeSimple(BaseModel):
    """用于列举可导入的委员会"""
    id: int
    name: str
    member_count: int = 0

    model_config = {"from_attributes": True}


class BulkImportFromCommittees(BaseModel):
    """从一个或多个委员会批量导入成员，自动去重"""
    committee_ids: list[int]
    channel: str | None = None
    assigned_to_id: int | None = None


# ─── CSV/Excel Import ─────────────────────────────────────────────────────────
# 前端上传 CSV 文件，每行代表一个人，必填列：display_name
# 可选列：email, phone, company, github_handle, notes

class CsvImportResult(BaseModel):
    created: int = 0
    matched: int = 0
    skipped: int = 0
    errors: list[str] = []


# ─── Campaign Task ─────────────────────────────────────────────────────────────────

VALID_TASK_STATUSES = {"not_started", "in_progress", "completed", "blocked"}
VALID_TASK_PRIORITIES = {"low", "medium", "high"}


class CampaignTaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "not_started"  # not_started / in_progress / completed / blocked
    priority: str = "medium"    # low / medium / high
    assignee_ids: list[int] = []
    deadline: date | None = None


class CampaignTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_ids: list[int] | None = None
    deadline: date | None = None


class CampaignTaskOut(BaseModel):
    id: int
    campaign_id: int
    title: str
    description: str | None
    status: str
    priority: str
    assignee_ids: list[int]
    deadline: date | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
