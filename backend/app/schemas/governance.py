from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


# ==================== Committee Schemas ====================

class CommitteeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = ""
    meeting_frequency: Optional[str] = None
    notification_email: Optional[str] = None
    notification_wechat: Optional[str] = None
    established_at: Optional[datetime] = None


class CommitteeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    meeting_frequency: Optional[str] = None
    notification_email: Optional[str] = None
    notification_wechat: Optional[str] = None
    established_at: Optional[datetime] = None


class CommitteeOut(BaseModel):
    id: int
    community_id: int
    name: str
    slug: str
    description: Optional[str] = ""
    is_active: bool
    meeting_frequency: Optional[str] = None
    notification_email: Optional[str] = None
    notification_wechat: Optional[str] = None
    established_at: Optional[datetime] = None
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
    email: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    organization: Optional[str] = None
    roles: list[str] = []
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    bio: Optional[str] = None


class CommitteeMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    organization: Optional[str] = None
    roles: Optional[list[str]] = None
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    is_active: Optional[bool] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class CommitteeMemberOut(BaseModel):
    id: int
    committee_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    organization: Optional[str] = None
    roles: list[str] = []
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    is_active: bool
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
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
    description: Optional[str] = None
    scheduled_at: datetime
    duration: int = Field(120, ge=1)
    location_type: Optional[str] = "online"
    location: Optional[str] = None
    agenda: Optional[str] = None
    reminder_before_hours: int = 24


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration: Optional[int] = Field(None, ge=1)
    location_type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    agenda: Optional[str] = None
    reminder_before_hours: Optional[int] = None


class MeetingOut(BaseModel):
    id: int
    committee_id: int
    community_id: int
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration: int
    location_type: Optional[str] = None
    location: Optional[str] = None
    status: str
    reminder_sent: bool
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingDetail(MeetingOut):
    agenda: Optional[str] = None
    minutes: Optional[str] = None
    attachments: list[dict] = []
    committee_name: str = ""


class MeetingMinutesUpdate(BaseModel):
    minutes: str


# ==================== MeetingReminder Schemas ====================

class MeetingReminderOut(BaseModel):
    id: int
    meeting_id: int
    reminder_type: str
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    notification_channels: list[str] = []
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
