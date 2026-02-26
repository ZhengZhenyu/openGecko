from app.schemas.auth import (
    InitialSetupRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    SystemStatusResponse,
    Token,
    TokenData,
    UserInfoResponse,
)
from app.schemas.community import (
    CommunityBrief,
    CommunityCreate,
    CommunityMemberAdd,
    CommunityOut,
    CommunityUpdate,
    CommunityWithMembers,
    CommunityWithRole,
    UserBrief,
)
from app.schemas.content import ContentCreate, ContentOut, ContentUpdate
from app.schemas.publish import PublishRecordOut, PublishRequest
from app.schemas.user import SelfProfileUpdate, UserBase, UserCreate, UserOut, UserUpdate

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
    "SelfProfileUpdate",
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
