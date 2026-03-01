"""趋势动量分析器。

从 EcosystemSnapshot 时序快照计算每个项目的动量方向和速度评分。
若快照数 < 2，返回 MomentumLevel.INSUFFICIENT，其余字段为 None。
"""
from sqlalchemy.orm import Session

from app.insights.schemas import MomentumLevel, ProjectTrend
from app.models.ecosystem import EcosystemProject, EcosystemSnapshot


def _velocity_score(old_val: int | None, new_val: int | None) -> float:
    """计算单指标环比增速，返回 -1.0 ~ 1.0。"""
    if old_val is None or new_val is None or old_val == 0:
        return 0.0
    return (new_val - old_val) / old_val


def _compute_momentum(score: float) -> MomentumLevel:
    if score >= 0.2:
        return MomentumLevel.ACCELERATING
    if score >= 0.05:
        return MomentumLevel.GROWING
    if score >= -0.05:
        return MomentumLevel.STABLE
    return MomentumLevel.DECLINING


def analyze_project(db: Session, project: EcosystemProject) -> ProjectTrend:
    """计算单个项目的趋势数据。"""
    snapshots = (
        db.query(EcosystemSnapshot)
        .filter(EcosystemSnapshot.project_id == project.id)
        .order_by(EcosystemSnapshot.snapshot_at.desc())
        .limit(2)
        .all()
    )

    if len(snapshots) < 2:
        latest = snapshots[0] if snapshots else None
        return ProjectTrend(
            project_id=project.id,
            project_name=project.name,
            momentum=MomentumLevel.INSUFFICIENT,
            velocity_score=0.0,
            star_growth_30d=None,
            contributor_growth_30d=None,
            active_contributors_30d=latest.active_contributors_30d if latest else None,
            pr_merged_30d=latest.pr_merged_30d if latest else None,
            snapshot_count=len(snapshots),
            latest_snapshot_at=latest.snapshot_at if latest else None,
        )

    # snapshots[0] 是最新，snapshots[1] 是前一个
    new, old = snapshots[0], snapshots[1]

    # 各指标环比增速（权重：贡献者 0.35 / PR 0.30 / star 0.20 / commits 0.15）
    contrib_v = _velocity_score(old.active_contributors_30d, new.active_contributors_30d)
    pr_v = _velocity_score(old.pr_merged_30d, new.pr_merged_30d)
    star_v = _velocity_score(old.stars, new.stars)
    commit_v = _velocity_score(old.commits_30d, new.commits_30d)

    composite = contrib_v * 0.35 + pr_v * 0.30 + star_v * 0.20 + commit_v * 0.15
    # 映射到 0–100 分：composite 范围大约 -1 ~ 1，线性缩放后截断
    velocity_score = max(0.0, min(100.0, (composite + 0.5) * 100))

    star_growth = (
        (new.stars - old.stars) if new.stars is not None and old.stars is not None else None
    )
    contrib_growth = (
        (new.active_contributors_30d - old.active_contributors_30d)
        if new.active_contributors_30d is not None and old.active_contributors_30d is not None
        else None
    )

    return ProjectTrend(
        project_id=project.id,
        project_name=project.name,
        momentum=_compute_momentum(composite),
        velocity_score=round(velocity_score, 1),
        star_growth_30d=star_growth,
        contributor_growth_30d=contrib_growth,
        active_contributors_30d=new.active_contributors_30d,
        pr_merged_30d=new.pr_merged_30d,
        snapshot_count=len(snapshots),
        latest_snapshot_at=new.snapshot_at,
    )


def analyze_all(db: Session) -> list[ProjectTrend]:
    """计算所有活跃项目的趋势数据，按 velocity_score 降序排列。"""
    projects = db.query(EcosystemProject).filter(EcosystemProject.is_active == True).all()  # noqa: E712
    results = [analyze_project(db, p) for p in projects]
    return sorted(results, key=lambda t: t.velocity_score, reverse=True)
