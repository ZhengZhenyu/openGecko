from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session, attributes

from app.core.dependencies import (
    get_community_admin,
    get_current_active_superuser,
    get_current_user,
    get_user_community_role,
)
from app.core.logging import get_logger
from app.database import get_db
from app.models import Community, User
from app.models.user import community_users
from app.schemas import (
    CommunityCreate,
    CommunityMemberAdd,
    CommunityOut,
    CommunityUpdate,
    CommunityWithMembers,
)
from app.schemas.community import PaginatedCommunities
from app.schemas.email import EmailSettings, EmailSettingsOut

router = APIRouter()
logger = get_logger(__name__)


class TestEmailRequest(BaseModel):
    to_email: str


@router.get("", response_model=PaginatedCommunities)
def list_communities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of communities accessible to current user.

    Superusers can see all communities.
    Regular users can only see communities they are members of.
    """
    if current_user.is_superuser:
        query = db.query(Community)
    else:
        query = db.query(Community).filter(
            Community.members.any(User.id == current_user.id)
        )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedCommunities(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=CommunityOut, status_code=status.HTTP_201_CREATED)
def create_community(
    community_create: CommunityCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Create a new community.

    Only superusers can create communities.

    Args:
        community_create: Community creation data
        current_user: Current authenticated superuser
        db: Database session

    Returns:
        CommunityOut: Created community

    Raises:
        HTTPException: If slug or name already exists
    """
    # Check if slug already exists
    existing_slug = db.query(Community).filter(Community.slug == community_create.slug).first()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Community slug already exists",
        )

    # Check if name already exists
    existing_name = db.query(Community).filter(Community.name == community_create.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Community name already exists",
        )

    # Create new community
    new_community = Community(**community_create.model_dump())
    db.add(new_community)
    db.flush()

    # Auto-add creator as community admin
    stmt = insert(community_users).values(
        user_id=current_user.id,
        community_id=new_community.id,
        role='admin'
    )
    db.execute(stmt)

    db.commit()
    db.refresh(new_community)

    return new_community


@router.get("/{community_id}", response_model=CommunityWithMembers)
def get_community(
    community_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get community details including members.

    Args:
        community_id: Community ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        CommunityWithMembers: Community with member list

    Raises:
        HTTPException: If community not found or user has no access
    """
    community = db.query(Community).filter(Community.id == community_id).first()

    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    # Check access rights
    if not current_user.is_superuser and community not in current_user.communities:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this community",
        )

    return community


@router.put("/{community_id}", response_model=CommunityOut)
def update_community(
    community_id: int,
    community_update: CommunityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update community information.

    Only superusers and community admins can update community information.
    """
    community = db.query(Community).filter(Community.id == community_id).first()

    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    # Check admin access rights
    role = get_user_community_role(current_user, community_id, db)
    if role not in ["superuser", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Community admin permissions required",
        )

    # Update fields
    update_data = community_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(community, field, value)

    db.commit()
    db.refresh(community)

    return community


class CommunityBasicUpdate(BaseModel):
    """社区基本信息更新（社区管理员可操作的字段）"""
    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    url: str | None = None


@router.put("/{community_id}/basic", response_model=CommunityOut)
def update_community_basic(
    community_id: int,
    data: CommunityBasicUpdate,
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """
    更新社区基本信息（名称、描述、Logo、官网链接）。

    社区管理员（Admin）和超级管理员（Superuser）均可操作。
    关键配置（SMTP、渠道凭证）请通过各自专用端点修改。
    """
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(community, field, value)

    db.commit()
    db.refresh(community)
    logger.info(
        "社区基本信息已更新",
        extra={"community_id": community_id, "updated_by": current_user.username},
    )
    return community


@router.delete("/{community_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_community(
    community_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Delete a community.

    Only superusers can delete communities.
    This will cascade delete all related data (contents, channel configs, etc.).

    Args:
        community_id: Community ID
        current_user: Current authenticated superuser
        db: Database session

    Raises:
        HTTPException: If community not found
    """
    community = db.query(Community).filter(Community.id == community_id).first()

    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    db.delete(community)
    db.commit()


@router.get("/{community_id}/users")
def get_community_users(
    community_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get users of a community with their roles.
    """
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    # Check access rights
    if not current_user.is_superuser and community not in current_user.communities:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this community",
        )

    # Query users with their roles
    stmt = (
        select(User, community_users.c.role)
        .join(community_users, User.id == community_users.c.user_id)
        .where(community_users.c.community_id == community_id)
    )
    results = db.execute(stmt).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name or "",
            "is_superuser": user.is_superuser,
            "role": role,
        }
        for user, role in results
    ]


@router.post("/{community_id}/users", response_model=CommunityWithMembers)
def add_user_to_community(
    community_id: int,
    member_add: CommunityMemberAdd,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Add a user to a community. Superuser only.
    """
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    user = db.query(User).filter(User.id == member_add.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user is already a member
    if user in community.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this community",
        )

    # Add user to community
    community.members.append(user)
    db.commit()
    db.refresh(community)
    return community


@router.delete("/{community_id}/users/{user_id}", status_code=status.HTTP_200_OK, response_model=CommunityWithMembers)
def remove_user_from_community(
    community_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Remove a user from a community. Superuser only.
    """
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user is a member
    if user not in community.members:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this community",
        )

    # Remove user from community
    community.members.remove(user)
    db.commit()
    db.refresh(community)
    return community


@router.put("/{community_id}/users/{user_id}/role", status_code=status.HTTP_200_OK)
def update_user_role(
    community_id: int,
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a user's role in a community.

    Community admins and superusers can update user roles.
    Valid roles: 'admin', 'user'
    """
    # 权限检查：社区管理员或超级管理员可操作
    caller_role = get_user_community_role(current_user, community_id, db)
    if caller_role not in ["superuser", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Community admin permissions required",
        )

    if role not in ['admin', 'user']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin' or 'user'",
        )

    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user is a member
    if user not in community.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this community",
        )

    # Update role in community_users table
    stmt = (
        update(community_users)
        .where(community_users.c.user_id == user_id)
        .where(community_users.c.community_id == community_id)
        .values(role=role)
    )
    db.execute(stmt)
    db.commit()

    return {"message": f"User role updated to {role} successfully"}


@router.get("/{community_id}/email-settings", response_model=EmailSettingsOut)
def get_email_settings(
    community_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """获取社区 SMTP 邮件配置（仅超级管理员可访问，凭证属于敏感信息）。"""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    # Check if user has access to this community
    if not current_user.is_superuser and community not in current_user.communities:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    settings_data = community.settings or {}
    email_config = settings_data.get("email") if isinstance(settings_data, dict) else None

    if not email_config:
        # Return default empty settings
        return EmailSettingsOut(
            enabled=False,
            provider="smtp",
            from_email="",
            smtp={}
        )

    # Return all SMTP config including password (admin has permission to view)
    smtp_config = email_config.get("smtp", {})
    if not isinstance(smtp_config, dict):
        smtp_config = {}

    return EmailSettingsOut(
        enabled=email_config.get("enabled", False),
        provider=email_config.get("provider", "smtp"),
        from_email=email_config.get("from_email", ""),
        from_name=email_config.get("from_name"),
        reply_to=email_config.get("reply_to"),
        smtp=smtp_config
    )


@router.put("/{community_id}/email-settings")
def update_email_settings(
    community_id: int,
    settings: EmailSettings,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """更新社区 SMTP 邮件配置（仅超级管理员可操作，避免 SMTP 凭证泄露）。"""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    # Check if user is admin of this community or superuser
    is_admin = False
    if current_user.is_superuser:
        is_admin = True
    else:
        # Check community_users role
        result = db.execute(
            select(community_users.c.role)
            .where(community_users.c.user_id == current_user.id)
            .where(community_users.c.community_id == community_id)
        ).first()
        if result and result[0] == 'admin':
            is_admin = True

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Update settings
    current_settings = community.settings or {}
    if not isinstance(current_settings, dict):
        current_settings = {}

    current_settings["email"] = settings.model_dump()
    community.settings = current_settings
    # Mark the JSON field as modified so SQLAlchemy detects the change
    attributes.flag_modified(community, "settings")

    db.commit()
    db.refresh(community)

    return {"message": "Email settings updated successfully"}


@router.post("/{community_id}/email-settings/test")
def test_email_settings(
    community_id: int,
    request_data: TestEmailRequest,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """发送 SMTP 测试邮件（仅超级管理员可操作）。"""
    to_email = request_data.to_email
    if not to_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="to_email is required",
        )

    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        )

    # Check if user is admin of this community or superuser
    is_admin = False
    if current_user.is_superuser:
        is_admin = True
    else:
        # Check community_users role
        result = db.execute(
            select(community_users.c.role)
            .where(community_users.c.user_id == current_user.id)
            .where(community_users.c.community_id == community_id)
        ).first()
        if result and result[0] == 'admin':
            is_admin = True

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Send test email
    from app.services.email import EmailMessage, get_sender_info, get_smtp_config, send_email

    smtp_config, email_cfg = get_smtp_config(community)
    if not smtp_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP not configured",
        )

    from_email, from_name, reply_to = get_sender_info(community, email_cfg)

    message = EmailMessage(
        subject=f"[{community.name}] Email Configuration Test",
        to_emails=[to_email],
        html_body="<html><body><h2>Email Test Successful!</h2><p>Your SMTP configuration is working correctly.</p></body></html>",
        text_body="Email Test Successful!\n\nYour SMTP configuration is working correctly.",
        from_email=from_email,
        from_name=from_name,
        reply_to=reply_to,
    )

    try:
        send_email(community, message)
        return {"message": "Test email sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        ) from e
