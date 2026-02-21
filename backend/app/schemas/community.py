from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CommunityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: str | None = ""
    url: str | None = None
    logo_url: str | None = None
    settings: dict[str, Any] | None = {}


class CommunityCreate(CommunityBase):
    pass


class CommunityUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    url: str | None = None
    logo_url: str | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


class CommunityBrief(BaseModel):
    """Brief community info for lists."""
    id: int
    name: str
    slug: str
    description: str | None = None
    url: str | None = None
    logo_url: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class PaginatedCommunities(BaseModel):
    """Paginated response for community list."""
    items: list[CommunityBrief]
    total: int
    page: int
    page_size: int


class CommunityWithRole(CommunityBrief):
    """Community info with user's role in it."""
    role: str  # 'admin' or 'user' or 'superuser' for superusers


class CommunityOut(CommunityBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommunityWithMembers(CommunityOut):
    """Community with member list."""
    members: list["UserBrief"] = []


class UserBrief(BaseModel):
    """Brief user info for lists."""
    id: int
    username: str
    email: str
    full_name: str | None = ""
    is_superuser: bool

    model_config = {"from_attributes": True}


class CommunityMemberAdd(BaseModel):
    """Request to add a user to a community."""
    user_id: int
    role: str = "member"


# Update forward references
CommunityWithMembers.model_rebuild()
