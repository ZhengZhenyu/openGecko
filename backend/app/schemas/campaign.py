from datetime import date, datetime

from pydantic import BaseModel

# ─── Campaign ─────────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    type: str  # promotion / care / invitation / survey
    description: str | None = None
    target_count: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    status: str | None = None   # draft / active / completed / archived
    target_count: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class CampaignListOut(BaseModel):
    id: int
    community_id: int
    name: str
    type: str
    status: str
    target_count: int | None
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
    responded: int = 0
    converted: int = 0
    declined: int = 0
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
