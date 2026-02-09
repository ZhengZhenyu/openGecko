from app.schemas.auth import (
    LoginRequest, Token, TokenData,
    InitialSetupRequest, PasswordResetRequest,
    PasswordResetConfirm, SystemStatusResponse,
    UserInfoResponse,
)
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserBase
from app.schemas.community import (
    CommunityCreate,
    CommunityUpdate,
    CommunityOut,
    CommunityBrief,
    CommunityWithRole,
    CommunityWithMembers,
    UserBrief,
    CommunityMemberAdd,
)
from app.schemas.content import ContentCreate, ContentUpdate, ContentOut
from app.schemas.publish import PublishRequest, PublishRecordOut

# Rebuild models with forward references now that all types are imported
UserInfoResponse.model_rebuild()
CommunityWithMembers.model_rebuild()

__all__ = [
    "LoginRequest",
    "Token",
    "TokenData",
    "InitialSetupRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "SystemStatusResponse",
    "UserInfoResponse",
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "UserBase",
    "CommunityCreate",
    "CommunityUpdate",
    "CommunityOut",
    "CommunityBrief",
    "CommunityWithRole",
    "CommunityWithMembers",
    "UserBrief",
    "CommunityMemberAdd",
    "ContentCreate",
    "ContentUpdate",
    "ContentOut",
    "PublishRequest",
    "PublishRecordOut",
]
