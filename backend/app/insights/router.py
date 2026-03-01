"""生态情报 API 路由。

前缀：/api/insights（在 main.py 中条件注册于 ENABLE_INSIGHTS_MODULE 块）。
所有端点均需认证（Depends(get_current_user)）。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.insights.analyzers import corporate as corporate_analyzer
from app.insights.analyzers import influence as influence_analyzer
from app.insights.analyzers import trend as trend_analyzer
from app.insights.schemas import CorporateLandscape, KeyPerson, MomentumLevel, ProjectTrend
from app.models.ecosystem import EcosystemProject
from app.models.user import User

router = APIRouter()


# ─── 趋势分析 ────────────────────────────────────────────────────────────────


@router.get("/trends", response_model=list[ProjectTrend], summary="所有项目趋势摘要")
def list_trends(
    momentum: MomentumLevel | None = Query(None, description="按动量级别筛选"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProjectTrend]:
    """返回所有活跃项目的趋势动量，按 velocity_score 降序排列。

    若尚无快照数据，momentum 为 `insufficient_data`。
    """
    results = trend_analyzer.analyze_all(db)
    if momentum is not None:
        results = [r for r in results if r.momentum == momentum]
    return results


@router.get("/trends/{project_id}", response_model=ProjectTrend, summary="单项目趋势详情")
def get_trend(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProjectTrend:
    project = db.get(EcosystemProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return trend_analyzer.analyze_project(db, project)


# ─── 关键人物 ─────────────────────────────────────────────────────────────────


@router.get("/people", response_model=list[KeyPerson], summary="关键人物列表")
def list_key_people(
    type: str | None = Query(None, description="按影响力类型筛选（maintainer/bridge/rising_star/reviewer/contributor）"),
    limit: int = Query(50, ge=1, le=200, description="最多返回条数"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[KeyPerson]:
    """返回贡献者影响力排行，跨项目聚合，按综合评分降序。

    未填充 company / review_count_90d 时相应字段为 null。
    """
    return influence_analyzer.analyze_all(db, influence_type=type, limit=limit)


@router.get("/people/{github_handle}", response_model=KeyPerson, summary="单人影响力画像")
def get_person(
    github_handle: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KeyPerson:
    result = influence_analyzer.analyze_person(db, github_handle)
    if result is None:
        raise HTTPException(status_code=404, detail="贡献者不存在")
    return result


# ─── 企业图谱 ─────────────────────────────────────────────────────────────────


@router.get("/corporate", response_model=list[CorporateLandscape], summary="企业生态图谱")
def list_corporate(
    min_projects: int = Query(1, ge=1, description="至少出现在 N 个项目中"),
    limit: int = Query(50, ge=1, le=200, description="最多返回条数"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CorporateLandscape]:
    """按企业聚合贡献数据，识别战略性投入生态的企业。

    company 字段来自 GitHub profile，由采集器填充后生效；未填充时返回空列表。
    """
    return corporate_analyzer.analyze_all(db, min_projects=min_projects, limit=limit)


@router.get("/corporate/{company}", response_model=CorporateLandscape, summary="单企业详情")
def get_corporate(
    company: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CorporateLandscape:
    result = corporate_analyzer.analyze_company(db, company)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该企业的贡献数据")
    return result
