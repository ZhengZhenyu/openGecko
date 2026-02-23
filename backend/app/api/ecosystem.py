from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.models.ecosystem import EcosystemContributor, EcosystemProject
from app.models.people import PersonProfile
from app.schemas.ecosystem import (
    PaginatedContributors,
    ProjectCreate,
    ProjectListOut,
    ProjectOut,
    ProjectUpdate,
    SyncResult,
)
from app.services.ecosystem.github_crawler import sync_project

router = APIRouter()

VALID_PLATFORMS = {"github", "gitee", "gitcode"}


# ─── Project CRUD ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[ProjectListOut])
def list_projects(
    community_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(EcosystemProject)
    if community_id is not None:
        query = query.filter(EcosystemProject.community_id == community_id)
    return query.order_by(EcosystemProject.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.platform not in VALID_PLATFORMS:
        raise HTTPException(400, f"platform 必须为 {VALID_PLATFORMS}")
    project = EcosystemProject(
        added_by_id=current_user.id,
        **data.model_dump(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{pid}", response_model=ProjectOut)
def get_project(
    pid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(EcosystemProject).filter(EcosystemProject.id == pid).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    return project


@router.patch("/{pid}", response_model=ProjectOut)
def update_project(
    pid: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(EcosystemProject).filter(EcosystemProject.id == pid).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


# ─── Sync ─────────────────────────────────────────────────────────────────────

@router.post("/{pid}/sync", response_model=SyncResult)
def trigger_sync(
    pid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发单个项目同步。"""
    project = db.query(EcosystemProject).filter(EcosystemProject.id == pid).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    token = getattr(settings, "GITHUB_PAT", None)
    result = sync_project(db, project, token)
    return result


# ─── Contributors ─────────────────────────────────────────────────────────────

@router.get("/{pid}/contributors", response_model=PaginatedContributors)
def list_contributors(
    pid: int,
    q: str | None = None,
    unlinked: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(EcosystemProject).filter(EcosystemProject.id == pid).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    query = db.query(EcosystemContributor).filter(EcosystemContributor.project_id == pid)
    if q:
        # 转义 LIKE 通配符，防止用户输入 % / _ 造成意外匹配
        q_escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(
            EcosystemContributor.github_handle.ilike(f"%{q_escaped}%")
            | EcosystemContributor.display_name.ilike(f"%{q_escaped}%")
        )
    if unlinked:
        query = query.filter(EcosystemContributor.person_id == None)  # noqa: E711
    query = query.order_by(EcosystemContributor.commit_count_90d.desc().nullslast())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedContributors(items=items, total=total, page=page, page_size=page_size)


@router.post("/{pid}/contributors/{handle}/import-person", status_code=200)
def import_contributor_to_people(
    pid: int,
    handle: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将贡献者导入人脉库，并关联 person_id。"""
    project = db.query(EcosystemProject).filter(EcosystemProject.id == pid).first()
    if not project:
        raise HTTPException(404, "项目不存在")

    contributor = db.query(EcosystemContributor).filter(
        EcosystemContributor.project_id == pid,
        EcosystemContributor.github_handle == handle,
    ).first()
    if not contributor:
        raise HTTPException(404, "贡献者不存在")

    # 尝试在人脉库查找同名 GitHub 账号
    existing = db.query(PersonProfile).filter(
        PersonProfile.github_handle == handle
    ).first()

    if existing:
        contributor.person_id = existing.id
        db.commit()
        return {"action": "linked", "person_id": existing.id}

    # 新建人脉档案
    person = PersonProfile(
        display_name=contributor.display_name or handle,
        github_handle=handle,
        avatar_url=contributor.avatar_url,
        source="ecosystem_import",
        created_by_id=current_user.id,
    )
    db.add(person)
    db.flush()
    contributor.person_id = person.id
    db.commit()
    return {"action": "created", "person_id": person.id}
