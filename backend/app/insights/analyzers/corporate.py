"""企业图谱分析器。

按 EcosystemContributor.company 字段聚合，识别在生态项目中战略性投入的企业。
company 字段来自 GitHub profile，由采集器填充；为空时返回空列表（优雅降级）。
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from app.insights.schemas import CorporateLandscape, ProjectPresence
from app.models.ecosystem import EcosystemContributor, EcosystemProject


def analyze_all(
    db: Session,
    min_projects: int = 1,
    limit: int = 50,
) -> list[CorporateLandscape]:
    """返回企业图谱列表，按 strategic_score 降序。

    Args:
        min_projects: 只返回至少出现在 N 个项目中的企业。
        limit: 最多返回条数。
    """
    # 只处理有 company 字段的 contributor
    contributors = (
        db.query(EcosystemContributor)
        .filter(
            EcosystemContributor.company.isnot(None),
            EcosystemContributor.company != "",
        )
        .all()
    )

    if not contributors:
        return []

    total_projects = db.query(EcosystemProject).filter(EcosystemProject.is_active == True).count()  # noqa: E712
    if total_projects == 0:
        return []

    # 按 (company, project_id) 分组
    # key: company → project_id → list[contributor]
    company_projects: dict[str, dict[int, list[EcosystemContributor]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for c in contributors:
        company_projects[c.company][c.project_id].append(c)

    # 预加载项目名称
    project_names: dict[int, str] = {
        p.id: p.name
        for p in db.query(EcosystemProject).filter(EcosystemProject.is_active == True).all()  # noqa: E712
    }

    # 计算各项目总 commit（用于 commit_share 分母）
    project_total_commits: dict[int, int] = defaultdict(int)
    for c in db.query(EcosystemContributor).all():
        project_total_commits[c.project_id] += c.commit_count_90d or 0

    results: list[CorporateLandscape] = []
    for company, proj_map in company_projects.items():
        if len(proj_map) < min_projects:
            continue

        presences: list[ProjectPresence] = []
        total_contributors = 0
        has_maintainer = False

        for project_id, members in proj_map.items():
            project_name = project_names.get(project_id, f"project-{project_id}")
            company_commits = sum((m.commit_count_90d or 0) for m in members)
            proj_total = project_total_commits.get(project_id, 0)
            commit_share = (company_commits / proj_total) if proj_total > 0 else 0.0
            has_maint = any(m.role == "maintainer" for m in members)

            if has_maint:
                has_maintainer = True
            total_contributors += len(members)

            presences.append(
                ProjectPresence(
                    project_id=project_id,
                    project_name=project_name,
                    contributor_count=len(members),
                    has_maintainer=has_maint,
                    commit_share=round(commit_share, 3),
                )
            )

        strategic_score = round((len(proj_map) / total_projects) * 100, 1)

        results.append(
            CorporateLandscape(
                company=company,
                project_count=len(proj_map),
                strategic_score=strategic_score,
                has_maintainer=has_maintainer,
                total_contributors=total_contributors,
                projects=sorted(presences, key=lambda p: p.contributor_count, reverse=True),
            )
        )

    results.sort(key=lambda r: r.strategic_score, reverse=True)
    return results[:limit]


def analyze_company(db: Session, company: str) -> CorporateLandscape | None:
    """返回单个企业的详情，不存在则返回 None。"""
    all_data = analyze_all(db, limit=10000)
    return next((r for r in all_data if r.company.lower() == company.lower()), None)
