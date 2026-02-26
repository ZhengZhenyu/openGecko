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


class SelfProfileUpdate(BaseModel):
    """用户自助修改个人资料（只允许修改非权限字段）"""
    full_name: str | None = Field(None, max_length=200)
    email: EmailStr | None = None
    current_password: str | None = Field(None, description="修改密码时必须提供当前密码")
    new_password: str | None = Field(None, min_length=6, max_length=100, description="新密码")


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}
