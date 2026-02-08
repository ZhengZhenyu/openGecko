from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class CommunityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = ""
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}


class CommunityCreate(CommunityBase):
    pass


class CommunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CommunityBrief(BaseModel):
    """Brief community info for lists."""
    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class CommunityOut(CommunityBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommunityWithMembers(CommunityOut):
    """Community with member list."""
    members: List["UserBrief"] = []


class UserBrief(BaseModel):
    """Brief user info for lists."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = ""
    is_superuser: bool

    model_config = {"from_attributes": True}


class CommunityMemberAdd(BaseModel):
    """Request to add a user to a community."""
    user_id: int
    role: str = "member"


# Update forward references
CommunityWithMembers.model_rebuild()
