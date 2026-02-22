from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.models.people import CommunityRole, PersonProfile
from app.schemas.people import (
    CommunityRoleCreate,
    CommunityRoleOut,
    MergeConfirm,
    PaginatedPeople,
    PersonCreate,
    PersonOut,
    PersonUpdate,
)
from app.services.people_service import find_or_suggest

router = APIRouter()


@router.get("", response_model=PaginatedPeople)
def list_people(
    q: str | None = None,
    tag: str | None = None,
    company: str | None = None,
    source: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(PersonProfile)
    if q:
        query = query.filter(
            PersonProfile.display_name.ilike(f"%{q}%")
            | PersonProfile.email.ilike(f"%{q}%")
            | PersonProfile.github_handle.ilike(f"%{q}%")
        )
    if tag:
        query = query.filter(PersonProfile.tags.contains([tag]))
    if company:
        query = query.filter(PersonProfile.company.ilike(f"%{company}%"))
    if source:
        query = query.filter(PersonProfile.source == source)
    total = query.count()
    items = query.order_by(PersonProfile.display_name).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedPeople(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=PersonOut, status_code=201)
def create_person(
    data: PersonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 检查唯一字段冲突
    if data.github_handle:
        if db.query(PersonProfile).filter(PersonProfile.github_handle == data.github_handle).first():
            raise HTTPException(400, "该 GitHub 账号已存在")
    if data.email:
        if db.query(PersonProfile).filter(PersonProfile.email == data.email).first():
            raise HTTPException(400, "该邮箱已存在")
    person = PersonProfile(**data.model_dump(), created_by_id=current_user.id)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonOut)
def get_person(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(PersonProfile).filter(PersonProfile.id == person_id).first()
    if not person:
        raise HTTPException(404, "人脉档案不存在")
    return person


@router.patch("/{person_id}", response_model=PersonOut)
def update_person(
    person_id: int,
    data: PersonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(PersonProfile).filter(PersonProfile.id == person_id).first()
    if not person:
        raise HTTPException(404, "人脉档案不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(person, key, value)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=204)
def delete_person(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(PersonProfile).filter(PersonProfile.id == person_id).first()
    if not person:
        raise HTTPException(404, "人脉档案不存在")
    db.delete(person)
    db.commit()


@router.get("/{person_id}/roles", response_model=list[CommunityRoleOut])
def list_roles(
    person_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(PersonProfile).filter(PersonProfile.id == person_id).first()
    if not person:
        raise HTTPException(404, "人脉档案不存在")
    return person.community_roles


@router.post("/{person_id}/roles", response_model=CommunityRoleOut, status_code=201)
def add_role(
    person_id: int,
    data: CommunityRoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    person = db.query(PersonProfile).filter(PersonProfile.id == person_id).first()
    if not person:
        raise HTTPException(404, "人脉档案不存在")
    role = CommunityRole(**data.model_dump(), person_id=person_id, updated_by_id=current_user.id)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.post("/import", status_code=200)
def import_people(
    rows: list[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量导入人脉（Excel/CSV 解析后的行数据列表）。

    返回每行的匹配结果，status 为 matched/suggest/new。
    """
    results = []
    for row in rows:
        match_result = find_or_suggest(db, row)
        results.append({"row": row, **match_result})
    return {"results": results, "total": len(results)}


@router.post("/confirm-merge", status_code=200)
def confirm_merge(
    data: MergeConfirm,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """确认/拒绝去重匹配结果。

    - confirmed=True + person_id: 将导入行关联到已有 PersonProfile
    - confirmed=True + person_id=None: 创建新 PersonProfile
    - confirmed=False: 跳过此行
    """
    if not data.confirmed:
        return {"action": "skipped"}

    if data.person_id is not None:
        person = db.query(PersonProfile).filter(PersonProfile.id == data.person_id).first()
        if not person:
            raise HTTPException(404, "人脉档案不存在")
        return {"action": "linked", "person_id": person.id}

    # 创建新档案
    row = data.import_row
    person = PersonProfile(
        display_name=row.get("display_name", ""),
        github_handle=row.get("github_handle") or None,
        email=row.get("email") or None,
        company=row.get("company") or None,
        source="event_import",
        created_by_id=current_user.id,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return {"action": "created", "person_id": person.id}
