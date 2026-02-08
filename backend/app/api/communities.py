from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_current_active_superuser
from app.database import get_db
from app.models import User, Community
from app.schemas import (
    CommunityCreate,
    CommunityUpdate,
    CommunityOut,
    CommunityBrief,
    CommunityWithMembers,
    CommunityMemberAdd,
)

router = APIRouter()


@router.get("", response_model=List[CommunityBrief])
def list_communities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of communities accessible to current user.

    Superusers can see all communities.
    Regular users can only see communities they are members of.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[CommunityBrief]: List of accessible communities
    """
    if current_user.is_superuser:
        # Superusers can see all communities
        communities = db.query(Community).all()
    else:
        # Regular users see only their communities
        communities = current_user.communities

    return communities


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

    Args:
        community_id: Community ID
        community_update: Community update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        CommunityOut: Updated community

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

    # Update fields
    update_data = community_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(community, field, value)

    db.commit()
    db.refresh(community)

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


@router.post("/{community_id}/users", status_code=status.HTTP_201_CREATED)
def add_user_to_community(
    community_id: int,
    member_add: CommunityMemberAdd,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Add a user to a community.

    Only superusers can manage community members.

    Args:
        community_id: Community ID
        member_add: Member addition data
        current_user: Current authenticated superuser
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If community or user not found, or user already a member
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

    return {"message": "User added to community successfully"}


@router.delete("/{community_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_from_community(
    community_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Remove a user from a community.

    Only superusers can manage community members.

    Args:
        community_id: Community ID
        user_id: User ID to remove
        current_user: Current authenticated superuser
        db: Database session

    Raises:
        HTTPException: If community or user not found, or user not a member
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this community",
        )

    # Remove user from community
    community.members.remove(user)
    db.commit()
