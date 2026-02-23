from datetime import date, datetime

from pydantic import BaseModel, Field

# ==================== Committee Schemas ====================

class CommitteeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: str | None = ""
    meeting_frequency: str | None = None
    notification_email: str | None = None
    notification_wechat: str | None = None
    established_at: datetime | None = None


class CommitteeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None
    meeting_frequency: str | None = None
    notification_email: str | None = None
    notification_wechat: str | None = None
    established_at: datetime | None = None


class CommitteeOut(BaseModel):
    id: int
    community_id: int
    name: str
    slug: str
    description: str | None = ""
    is_active: bool
    meeting_frequency: str | None = None
    notification_email: str | None = None
    notification_wechat: str | None = None
    established_at: datetime | None = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommitteeBrief(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    member_count: int = 0

    model_config = {"from_attributes": True}


# ==================== CommitteeMember Schemas ====================

class CommitteeMemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(None, max_length=200)
    phone: str | None = None
    wechat: str | None = None
    organization: str | None = Field(None, max_length=200)
    gitcode_id: str | None = None
    github_id: str | None = None
    roles: list[str] = []
    term_start: date | None = None
    term_end: date | None = None
    bio: str | None = None


class CommitteeMemberUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    email: str | None = Field(None, min_length=1, max_length=200)
    phone: str | None = None
    wechat: str | None = None
    organization: str | None = Field(None, min_length=1, max_length=200)
    gitcode_id: str | None = None
    github_id: str | None = None
    roles: list[str] | None = None
    term_start: date | None = None
    term_end: date | None = None
    is_active: bool | None = None
    bio: str | None = None
    avatar_url: str | None = None


class CommitteeMemberOut(BaseModel):
    id: int
    committee_id: int
    name: str
    email: str | None = None
    phone: str | None = None
    wechat: str | None = None
    organization: str | None = None
    gitcode_id: str | None = None
    github_id: str | None = None
    roles: list[str] = []
    term_start: date | None = None
    term_end: date | None = None
    is_active: bool
    bio: str | None = None
    avatar_url: str | None = None
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommitteeWithMembers(CommitteeOut):
    members: list[CommitteeMemberOut] = []


class BatchImportResult(BaseModel):
    success: int
    failed: int
    errors: list[str] = []
    imported_members: list[CommitteeMemberOut] = []


# ==================== Meeting Schemas ====================

class MeetingCreate(BaseModel):
    committee_id: int
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    scheduled_at: datetime
    duration: int = Field(120, ge=1)
    location_type: str | None = "online"
    location: str | None = None        # 线下会议地址（offline / hybrid）
    online_url: str | None = None      # 线上会议链接（online / hybrid）
    agenda: str | None = None
    reminder_before_hours: int = 24
    assignee_ids: list[int] = []


class MeetingUpdate(BaseModel):
    committee_id: int | None = None
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    scheduled_at: datetime | None = None
    duration: int | None = Field(None, ge=1)
    location_type: str | None = None
    location: str | None = None        # 线下会议地址（offline / hybrid）
    online_url: str | None = None      # 线上会议链接（online / hybrid）
    status: str | None = None
    agenda: str | None = None
    reminder_before_hours: int | None = None
    assignee_ids: list[int] | None = None


class MeetingOut(BaseModel):
    id: int
    committee_id: int
    community_id: int
    title: str
    description: str | None = None
    scheduled_at: datetime
    duration: int
    location_type: str | None = None
    location: str | None = None
    online_url: str | None = None
    status: str
    reminder_sent: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    assignee_ids: list[int] = []

    model_config = {"from_attributes": True}


class MeetingDetail(MeetingOut):
    agenda: str | None = None
    minutes: str | None = None
    attachments: list[dict] = []
    committee_name: str = ""


class MeetingMinutesUpdate(BaseModel):
    minutes: str


class MeetingParticipantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=1, max_length=200)


class MeetingParticipantOut(BaseModel):
    id: int
    meeting_id: int
    name: str
    email: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingParticipantImportResult(BaseModel):
    imported: int
    skipped: int
    participants: list[MeetingParticipantOut] = []


# ==================== MeetingReminder Schemas ====================

class MeetingReminderCreate(BaseModel):
    reminder_type: str = Field(..., description="Reminder type: preparation, one_week, three_days, one_day, two_hours, immediate")


class MeetingReminderOut(BaseModel):
    id: int
    meeting_id: int
    reminder_type: str
    scheduled_at: datetime
    sent_at: datetime | None = None
    notification_channels: list[str] = []
    status: str
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
