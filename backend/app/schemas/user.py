from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str | None = ""


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    is_superuser: bool | None = False  # Only superusers can set this to True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=6, max_length=100)
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}
