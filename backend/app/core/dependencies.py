
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import Community, User
from app.models.user import community_users


async def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_community(
    x_community_id: int | None = Header(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    """
    Dependency to get and validate the current community ID.

    Args:
        x_community_id: Community ID from X-Community-Id header
        user: Current authenticated user
        db: Database session

    Returns:
        int: The validated community ID

    Raises:
        HTTPException: If community ID is missing or user has no access
    """
    if x_community_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Community-Id header is required",
        )

    # Superusers can access all communities
    if user.is_superuser:
        # Verify community exists
        community = db.query(Community).filter(Community.id == x_community_id).first()
        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )
        return x_community_id

    # Regular users can only access their assigned communities
    community = (
        db.query(Community)
        .filter(Community.id == x_community_id)
        .filter(Community.members.contains(user))
        .first()
    )

    if not community:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this community",
        )

    return x_community_id


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to verify the current user is a superuser.

    Args:
        current_user: Current authenticated user

    Returns:
        User: The superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_user_community_role(
    user: User,
    community_id: int,
    db: Session,
) -> str | None:
    """
    Get user's role in a specific community.

    Args:
        user: User object
        community_id: Community ID
        db: Database session

    Returns:
        str: User role ('admin' or 'user') or None if not a member
    """
    if user.is_superuser:
        return "superuser"

    # Query the community_users table for the role
    stmt = select(community_users.c.role).where(
        community_users.c.user_id == user.id,
        community_users.c.community_id == community_id
    )
    result = db.execute(stmt).scalar()
    return result


async def get_current_admin_or_superuser(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to verify user is a platform admin or superuser.

    Checks if the user is a superuser OR has 'admin' role in any community.
    Used for platform-level management operations (community settings, analytics config, etc.)

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User: The admin/superuser user

    Raises:
        HTTPException: If user does not have admin or superuser permissions
    """
    if current_user.is_superuser:
        return current_user

    stmt = select(community_users.c.role).where(
        community_users.c.user_id == current_user.id,
        community_users.c.role == "admin",
    ).limit(1)
    result = db.execute(stmt).scalar()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员权限不足",
        )

    return current_user


async def get_community_admin(
    x_community_id: int | None = Header(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to verify user is a community admin or superuser.

    Deprecated: Use get_current_admin_or_superuser for platform-level checks,
    or get_current_user for business operations (committees, meetings, etc.)
    kept for backward compatibility during the transition period.

    Args:
        x_community_id: Community ID from header
        user: Current authenticated user
        db: Database session

    Returns:
        User: The admin user

    Raises:
        HTTPException: If user is not an admin of the community
    """
    if x_community_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Community-Id header is required",
        )

    role = get_user_community_role(user, x_community_id, db)

    if role not in ["superuser", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Community admin permissions required",
        )

    return user


def check_content_edit_permission(
    content,
    user: User,
    db: Session,
) -> bool:
    """
    Check if user has permission to edit a content.

    Rules:
    - Owner can always edit
    - Collaborators can always edit
    - Community admins can edit
    - Superusers can edit

    Args:
        content: Content object
        user: User object
        db: Database session

    Returns:
        bool: True if user can edit
    """
    # Superuser can edit anything
    if user.is_superuser:
        return True

    # Owner can edit
    if content.owner_id == user.id:
        return True

    # Collaborators can edit
    if user in content.collaborators:
        return True

    # Community admin can edit
    role = get_user_community_role(user, content.community_id, db)
    if role == "admin":
        return True

    return False
