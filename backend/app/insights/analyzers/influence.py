"""关键人物影响力分析器。

基于 EcosystemContributor 现有数据识别维护者、跨项目连接者、崛起者、Reviewer。
无需 EcosystemSnapshot，可立即提供洞察（尽管数据完整度依赖采集器后续填充）。
"""
from collections import defaultdict
from datetime import UTC, timedelta

from sqlalchemy.orm import Session

from app.core.timezone import utc_now
from app.insights.schemas import InfluenceType, KeyPerson
from app.models.ecosystem import EcosystemContributor

_RISING_STAR_DAYS = 90          # 首次贡献在多少天内算"崛起者"
_RISING_STAR_MIN_COMMITS = 5    # 崛起者最低 commit 数
_REVIEWER_MIN_REVIEWS = 5       # 被标记为 Reviewer 的最低 review 次数
_BRIDGE_MIN_PROJECTS = 2        # 跨项目连接者最少活跃项目数


def _score(commits: int, prs: int, reviews: int, cross_project_count: int) -> float:
    """0–100 综合影响力评分（加权）。"""
    c = min(commits, 500)
    p = min(prs, 200)
    r = min(reviews, 200)
    cross = min(cross_project_count, 10)

    # 各维度归一化后加权
    score = (
        (c / 500) * 30
        + (p / 200) * 30
        + (r / 200) * 20
        + (cross / 10) * 20
    )
    return round(score, 1)


def _classify(
    contributor: EcosystemContributor,
    cross_project_count: int,
    total_commits: int,
    total_reviews: int,
) -> list[InfluenceType]:
    types: list[InfluenceType] = []

    if contributor.role == "maintainer":
        types.append(InfluenceType.MAINTAINER)

    if cross_project_count >= _BRIDGE_MIN_PROJECTS:
        types.append(InfluenceType.BRIDGE)

    first = contributor.first_contributed_at
    if first is not None and first.tzinfo is None:
        first = first.replace(tzinfo=UTC)
    if (
        first is not None
        and first >= utc_now() - timedelta(days=_RISING_STAR_DAYS)
        and total_commits >= _RISING_STAR_MIN_COMMITS
    ):
        types.append(InfluenceType.RISING_STAR)

    if total_reviews >= _REVIEWER_MIN_REVIEWS:
        types.append(InfluenceType.REVIEWER)

    if not types:
        types.append(InfluenceType.CONTRIBUTOR)

    return types


def analyze_all(
    db: Session,
    influence_type: str | None = None,
    limit: int = 50,
) -> list[KeyPerson]:
    """返回关键人物列表，按 influence_score 降序。

    Args:
        influence_type: 按类型筛选（InfluenceType 值），None 表示不筛选。
        limit: 最多返回条数。
    """
    contributors = db.query(EcosystemContributor).all()

    # 聚合：同一 github_handle 可能出现在多个项目
    by_handle: dict[str, list[EcosystemContributor]] = defaultdict(list)
    for c in contributors:
        by_handle[c.github_handle].append(c)

    results: list[KeyPerson] = []
    for handle, records in by_handle.items():
        # 取各项目数据的合并值（commit 相加，profile 取第一个非 None 值）
        total_commits = sum((r.commit_count_90d or 0) for r in records)
        total_prs = sum((r.pr_count_90d or 0) for r in records)
        total_reviews = sum((r.review_count_90d or 0) for r in records)
        cross_count = len({r.project_id for r in records})
        project_ids = list({r.project_id for r in records})

        # 取 profile 字段（按非 None 优先）
        first_rec = next((r for r in records if r.display_name), records[0])
        company = next((r.company for r in records if r.company), None)
        person_id = next((r.person_id for r in records if r.person_id), None)

        # 以 commit 最多的记录作为代表（仅用于读取 role / first_contributed_at）
        rep = max(records, key=lambda r: r.commit_count_90d or 0)

        types = _classify(rep, cross_count, total_commits, total_reviews)

        # 类型过滤
        if influence_type and InfluenceType(influence_type) not in types:
            continue

        results.append(
            KeyPerson(
                github_handle=handle,
                display_name=first_rec.display_name,
                avatar_url=first_rec.avatar_url,
                influence_types=types,
                influence_score=_score(total_commits, total_prs, total_reviews, cross_count),
                cross_project_count=cross_count,
                commit_count_90d=total_commits or None,
                pr_count_90d=total_prs or None,
                review_count_90d=total_reviews or None,
                company=company,
                person_profile_id=person_id,
                project_ids=project_ids,
            )
        )

    results.sort(key=lambda p: p.influence_score, reverse=True)
    return results[:limit]


def analyze_person(db: Session, github_handle: str) -> KeyPerson | None:
    """返回单个贡献者的影响力画像，不存在则返回 None。"""
    records = (
        db.query(EcosystemContributor)
        .filter(EcosystemContributor.github_handle == github_handle)
        .all()
    )
    if not records:
        return None

    all_people = analyze_all(db, limit=10000)
    return next((p for p in all_people if p.github_handle == github_handle), None)
