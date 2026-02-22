from datetime import date, datetime

from pydantic import BaseModel


class CommunityRoleCreate(BaseModel):
    community_name: str
    project_url: str | None = None
    role: str
    role_label: str | None = None
    is_current: bool = True
    started_at: date | None = None
    ended_at: date | None = None
    source_url: str | None = None


class CommunityRoleOut(BaseModel):
    id: int
    community_name: str
    project_url: str | None
    role: str
    role_label: str | None
    is_current: bool
    started_at: date | None
    ended_at: date | None
    source_url: str | None

    model_config = {"from_attributes": True}


class PersonCreate(BaseModel):
    display_name: str
    avatar_url: str | None = None
    github_handle: str | None = None
    gitcode_handle: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    location: str | None = None
    bio: str | None = None
    tags: list[str] = []
    notes: str | None = None
    source: str = "manual"


class PersonUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    github_handle: str | None = None
    gitcode_handle: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    location: str | None = None
    bio: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class PersonOut(BaseModel):
    id: int
    display_name: str
    avatar_url: str | None
    github_handle: str | None
    gitcode_handle: str | None
    email: str | None
    phone: str | None
    company: str | None
    location: str | None
    bio: str | None
    tags: list[str]
    notes: str | None
    source: str
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime
    community_roles: list[CommunityRoleOut] = []

    model_config = {"from_attributes": True}


class PersonListOut(BaseModel):
    id: int
    display_name: str
    avatar_url: str | None
    github_handle: str | None
    email: str | None
    company: str | None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedPeople(BaseModel):
    items: list[PersonListOut]
    total: int
    page: int
    page_size: int


class MergeConfirm(BaseModel):
    """确认/拒绝去重匹配"""
    import_row: dict
    person_id: int | None  # None 表示创建新档案
    confirmed: bool
