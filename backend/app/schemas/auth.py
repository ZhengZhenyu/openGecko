from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field

if TYPE_CHECKING:
    from app.schemas.user import UserOut
    from app.schemas.community import CommunityWithRole


class LoginRequest(BaseModel):
    """Login request with username and password."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    is_default_admin: bool = False  # Indicates if this is the default admin (needs setup)


class TokenData(BaseModel):
    """Data encoded in JWT token."""
    username: str


class UserInfoResponse(BaseModel):
    """Response containing user info and their communities with roles."""
    user: "UserOut"
    communities: List["CommunityWithRole"]


class InitialSetupRequest(BaseModel):
    """Request to create a new admin account during initial setup."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = ""


class PasswordResetRequest(BaseModel):
    """Request a password reset email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token and new password."""
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)


class SystemStatusResponse(BaseModel):
    """System initialization status."""
    needs_setup: bool
    message: str


# Avoid circular imports - don't call model_rebuild here
# It will be called after all schemas are imported in __init__.py
if not TYPE_CHECKING:
    from app.schemas.user import UserOut  # noqa: F401
    from app.schemas.community import CommunityWithRole  # noqa: F401
