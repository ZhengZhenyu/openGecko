from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    get_current_community,
    get_community_admin,
)
from app.database import get_db
from app.models import User, Committee, CommitteeMember
from app.schemas.governance import (
    CommitteeCreate,
    CommitteeUpdate,
    CommitteeOut,
    CommitteeWithMembers,
    CommitteeMemberCreate,
    CommitteeMemberUpdate,
    CommitteeMemberOut,
)

router = APIRouter()


# ==================== Helper ====================

def _get_committee_or_404(
    committee_id: int,
    community_id: int,
    db: Session,
) -> Committee:
    committee = (
        db.query(Committee)
        .filter(
            Committee.id == committee_id,
            Committee.community_id == community_id,
        )
        .first()
    )
    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee not found",
        )
    return committee


def _committee_to_out(committee: Committee) -> dict:
    """Convert Committee model to dict with member_count."""
    return {
        **{c.key: getattr(committee, c.key) for c in committee.__table__.columns},
        "member_count": len(committee.members),
    }


# ==================== Committee CRUD ====================

@router.get("", response_model=List[CommitteeOut])
def list_committees(
    community_id: int = Depends(get_current_community),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """获取当前社区的委员会列表。"""
    query = db.query(Committee).filter(Committee.community_id == community_id)
    if is_active is not None:
        query = query.filter(Committee.is_active == is_active)
    committees = query.order_by(Committee.created_at.desc()).all()
    return [_committee_to_out(c) for c in committees]


@router.post("", response_model=CommitteeOut, status_code=status.HTTP_201_CREATED)
def create_committee(
    data: CommitteeCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """创建委员会（需要社区管理员权限）。"""
    # Check slug uniqueness within community
    existing = (
        db.query(Committee)
        .filter(
            Committee.community_id == community_id,
            Committee.slug == data.slug,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Committee slug already exists in this community",
        )

    committee = Committee(
        community_id=community_id,
        **data.model_dump(),
    )
    db.add(committee)
    db.commit()
    db.refresh(committee)
    return _committee_to_out(committee)


@router.get("/{committee_id}", response_model=CommitteeWithMembers)
def get_committee(
    committee_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """获取委员会详情，包含所有成员信息。"""
    committee = _get_committee_or_404(committee_id, community_id, db)
    result = _committee_to_out(committee)
    result["members"] = committee.members
    return result


@router.put("/{committee_id}", response_model=CommitteeOut)
def update_committee(
    committee_id: int,
    data: CommitteeUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """更新委员会信息（需要社区管理员权限）。"""
    committee = _get_committee_or_404(committee_id, community_id, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(committee, field, value)

    db.commit()
    db.refresh(committee)
    return _committee_to_out(committee)


@router.delete("/{committee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_committee(
    committee_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """删除委员会（需要社区管理员权限，级联删除成员和会议）。"""
    committee = _get_committee_or_404(committee_id, community_id, db)
    db.delete(committee)
    db.commit()


# ==================== Member Management ====================

@router.get("/{committee_id}/members", response_model=List[CommitteeMemberOut])
def list_members(
    committee_id: int,
    community_id: int = Depends(get_current_community),
    role: Optional[str] = Query(None, description="按角色筛选"),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """获取委员会成员列表。"""
    committee = _get_committee_or_404(committee_id, community_id, db)

    query = db.query(CommitteeMember).filter(
        CommitteeMember.committee_id == committee.id,
    )
    if is_active is not None:
        query = query.filter(CommitteeMember.is_active == is_active)

    members = query.order_by(CommitteeMember.joined_at.asc()).all()

    if role is not None:
        members = [m for m in members if role in (m.roles or [])]

    return members


@router.post(
    "/{committee_id}/members",
    response_model=CommitteeMemberOut,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    committee_id: int,
    data: CommitteeMemberCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """添加委员会成员（需要社区管理员权限）。"""
    committee = _get_committee_or_404(committee_id, community_id, db)

    member = CommitteeMember(
        committee_id=committee.id,
        **data.model_dump(),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get(
    "/{committee_id}/members/{member_id}",
    response_model=CommitteeMemberOut,
)
def get_member(
    committee_id: int,
    member_id: int,
    community_id: int = Depends(get_current_community),
    db: Session = Depends(get_db),
):
    """获取成员详情。"""
    _get_committee_or_404(committee_id, community_id, db)

    member = (
        db.query(CommitteeMember)
        .filter(
            CommitteeMember.id == member_id,
            CommitteeMember.committee_id == committee_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member


@router.put(
    "/{committee_id}/members/{member_id}",
    response_model=CommitteeMemberOut,
)
def update_member(
    committee_id: int,
    member_id: int,
    data: CommitteeMemberUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """更新成员信息（需要社区管理员权限）。"""
    _get_committee_or_404(committee_id, community_id, db)

    member = (
        db.query(CommitteeMember)
        .filter(
            CommitteeMember.id == member_id,
            CommitteeMember.committee_id == committee_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/{committee_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    committee_id: int,
    member_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """移除委员会成员（需要社区管理员权限）。"""
    _get_committee_or_404(committee_id, community_id, db)

    member = (
        db.query(CommitteeMember)
        .filter(
            CommitteeMember.id == member_id,
            CommitteeMember.committee_id == committee_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    db.delete(member)
    db.commit()
