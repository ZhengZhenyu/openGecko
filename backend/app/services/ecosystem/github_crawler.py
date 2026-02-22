"""GitHub 生态项目贡献者采集服务。

通过 GitHub REST API 获取指定仓库的贡献者列表，
写入 EcosystemContributor 表并更新 EcosystemProject.last_synced_at。
"""

import logging
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models.ecosystem import EcosystemContributor, EcosystemProject

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def _build_headers(token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def sync_project(db: Session, project: EcosystemProject, token: str | None = None) -> dict:
    """同步单个项目的贡献者数据。

    返回 {"created": int, "updated": int, "errors": int}。
    """
    if project.platform != "github":
        logger.info("跳过非 GitHub 项目: %s", project.name)
        return {"created": 0, "updated": 0, "errors": 0}

    headers = _build_headers(token)
    url = f"{GITHUB_API}/repos/{project.org_name}/{project.repo_name}/contributors"

    created = updated = errors = 0
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=headers, params={"per_page": 100, "anon": "false"})
            if resp.status_code != 200:
                logger.warning("GitHub API %s → %s", url, resp.status_code)
                return {"created": 0, "updated": 0, "errors": 1}

            existing_map = {c.github_handle: c for c in project.contributors}

            for item in resp.json():
                handle = item.get("login")
                if not handle:
                    continue
                if handle in existing_map:
                    existing_map[handle].commit_count_90d = item.get("contributions")
                    existing_map[handle].display_name = item.get("login")
                    existing_map[handle].avatar_url = item.get("avatar_url")
                    existing_map[handle].last_synced_at = datetime.utcnow()
                    updated += 1
                else:
                    db.add(EcosystemContributor(
                        project_id=project.id,
                        github_handle=handle,
                        display_name=item.get("login"),
                        avatar_url=item.get("avatar_url"),
                        commit_count_90d=item.get("contributions"),
                        last_synced_at=datetime.utcnow(),
                    ))
                    created += 1

    except Exception as exc:
        logger.error("同步项目 %s 失败: %s", project.name, exc)
        errors += 1
        return {"created": created, "updated": updated, "errors": errors}

    project.last_synced_at = datetime.utcnow()
    db.commit()
    logger.info("项目 %s 同步完成 — created=%d updated=%d", project.name, created, updated)
    return {"created": created, "updated": updated, "errors": errors}


def sync_all_projects(db: Session, token: str | None = None) -> dict:
    """同步所有活跃项目（APScheduler 定时调用）。"""
    projects = db.query(EcosystemProject).filter(EcosystemProject.is_active == True).all()  # noqa: E712
    total_created = total_updated = total_errors = 0
    for project in projects:
        result = sync_project(db, project, token)
        total_created += result["created"]
        total_updated += result["updated"]
        total_errors += result["errors"]
    return {"created": total_created, "updated": total_updated, "errors": total_errors}
