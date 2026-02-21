import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_community_admin,
    get_current_community,
)
from app.database import get_db
from app.models import Committee, CommitteeMember, User
from app.schemas.governance import (
    CommitteeCreate,
    CommitteeMemberCreate,
    CommitteeMemberOut,
    CommitteeMemberUpdate,
    CommitteeOut,
    CommitteeUpdate,
    CommitteeWithMembers,
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

@router.get("", response_model=list[CommitteeOut])
def list_committees(
    community_id: int = Depends(get_current_community),
    is_active: bool | None = Query(None),
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

@router.get("/{committee_id}/members", response_model=list[CommitteeMemberOut])
def list_members(
    committee_id: int,
    community_id: int = Depends(get_current_community),
    role: str | None = Query(None, description="按角色筛选"),
    is_active: bool | None = Query(None),
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


# ==================== CSV Import/Export ====================

@router.get("/{committee_id}/members/export")
def export_members_csv(
    committee_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """导出委员会成员为CSV文件（需要社区管理员权限）。"""
    committee = _get_committee_or_404(committee_id, community_id, db)

    members = (
        db.query(CommitteeMember)
        .filter(CommitteeMember.committee_id == committee_id)
        .all()
    )

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'name', 'email', 'phone', 'wechat', 'organization',
        'roles', 'term_start', 'term_end', 'is_active', 'bio'
    ])

    # Write data
    for member in members:
        writer.writerow([
            member.name,
            member.email or '',
            member.phone or '',
            member.wechat or '',
            member.organization or '',
            ','.join(member.roles) if member.roles else '',
            member.term_start.isoformat() if member.term_start else '',
            member.term_end.isoformat() if member.term_end else '',
            'true' if member.is_active else 'false',
            member.bio or ''
        ])

    # Prepare response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={committee.slug}_members.csv"
        }
    )


@router.post("/{committee_id}/members/import")
def import_members_csv(
    committee_id: int,
    file: UploadFile = File(...),
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_community_admin),
    db: Session = Depends(get_db),
):
    """从CSV文件批量导入委员会成员（需要社区管理员权限）。

    CSV格式要求：
    - 第一行为表头（name, email, phone, wechat, organization, roles, term_start, term_end, is_active, bio）
    - name 为必填字段
    - roles 用逗号分隔（如：chair,secretary）
    - term_start/term_end 格式：YYYY-MM-DD
    - is_active: true/false

    返回导入结果统计。
    """
    _get_committee_or_404(committee_id, community_id, db)

    # Check file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    # Read CSV content
    try:
        content = file.file.read().decode('utf-8-sig')  # Handle BOM
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(e)}"
        ) from e

    # Validate required fields
    required_fields = {'name'}
    if not required_fields.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV must contain required fields: {', '.join(required_fields)}"
        )

    # Process rows
    success_count = 0
    error_count = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):  # Start from 2 (1 is header)
        try:
            # Validate name
            name = row.get('name', '').strip()
            if not name:
                errors.append(f"Row {row_num}: name is required")
                error_count += 1
                continue

            # Parse roles
            roles_str = row.get('roles', '').strip()
            roles = [r.strip() for r in roles_str.split(',') if r.strip()] if roles_str else []

            # Parse dates
            term_start = None
            term_start_str = row.get('term_start', '').strip()
            if term_start_str:
                try:
                    term_start = date.fromisoformat(term_start_str)
                except ValueError:
                    errors.append(f"Row {row_num}: invalid term_start format (use YYYY-MM-DD)")
                    error_count += 1
                    continue

            term_end = None
            term_end_str = row.get('term_end', '').strip()
            if term_end_str:
                try:
                    term_end = date.fromisoformat(term_end_str)
                except ValueError:
                    errors.append(f"Row {row_num}: invalid term_end format (use YYYY-MM-DD)")
                    error_count += 1
                    continue

            # Parse is_active
            is_active_str = row.get('is_active', 'true').strip().lower()
            is_active = is_active_str in ('true', '1', 'yes', 'y')

            # Check for duplicate name in committee
            existing = (
                db.query(CommitteeMember)
                .filter(
                    CommitteeMember.committee_id == committee_id,
                    CommitteeMember.name == name
                )
                .first()
            )

            if existing:
                errors.append(f"Row {row_num}: member '{name}' already exists")
                error_count += 1
                continue

            # Create member
            member = CommitteeMember(
                committee_id=committee_id,
                name=name,
                email=row.get('email', '').strip() or None,
                phone=row.get('phone', '').strip() or None,
                wechat=row.get('wechat', '').strip() or None,
                organization=row.get('organization', '').strip() or None,
                roles=roles,
                term_start=term_start,
                term_end=term_end,
                is_active=is_active,
                bio=row.get('bio', '').strip() or None
            )

            db.add(member)
            success_count += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            error_count += 1

    # Commit all successful imports
    if success_count > 0:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save members: {str(e)}"
            ) from e

    return {
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors[:10] if errors else []  # Limit to first 10 errors
    }
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


