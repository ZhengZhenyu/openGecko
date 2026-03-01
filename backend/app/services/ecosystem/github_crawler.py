"""GitHub 生态项目采集服务（HTTP 层）。

职责：向 GitHub REST API 发起请求，将结果写入数据库。
不包含调度逻辑——调度与并发由 sync_worker.py 负责。
"""

import logging
import time
from datetime import timedelta

import httpx
from sqlalchemy.orm import Session

from app.core.timezone import utc_now
from app.models.ecosystem import EcosystemContributor, EcosystemProject, EcosystemSnapshot

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

# 快照写入最小间隔（23h），防止同一天重复写入
_SNAPSHOT_MIN_INTERVAL_HOURS = 23


# ─── 内部 HTTP 辅助 ────────────────────────────────────────────────────────────


def _build_headers(token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_json(
    client: httpx.Client, url: str, headers: dict, params: dict | None = None
) -> dict | list | None:
    """发起 GET 请求；非 200 时记录警告并返回 None。"""
    try:
        resp = client.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("GitHub API %s → %s", url, resp.status_code)
        return None
    except Exception as exc:
        logger.error("请求失败 %s: %s", url, exc)
        return None


def _get_stats_json(
    client: httpx.Client, url: str, headers: dict
) -> dict | list | None:
    """获取 GitHub stats 端点（可能返回 202 Computing）；202 时等待 3s 重试一次。"""
    try:
        resp = client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 202:
            time.sleep(3)
            resp2 = client.get(url, headers=headers)
            if resp2.status_code == 200:
                return resp2.json()
            logger.info("GitHub stats %s 仍在计算（202），跳过", url)
            return None
        logger.warning("GitHub stats %s → %s", url, resp.status_code)
        return None
    except Exception as exc:
        logger.error("请求失败 %s: %s", url, exc)
        return None


# ─── 快照数据抓取函数 ──────────────────────────────────────────────────────────


def _fetch_repo_stats(
    client: httpx.Client, org: str, repo: str, headers: dict
) -> dict:
    """GET /repos/{org}/{repo} → {stars, forks, open_issues, open_prs}。失败时各字段返回 None。"""
    data = _get_json(client, f"{GITHUB_API}/repos/{org}/{repo}", headers)
    if not data or not isinstance(data, dict):
        return {"stars": None, "forks": None, "open_issues": None, "open_prs": None}
    return {
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "open_prs": None,  # open PR count requires separate call; leave for future
    }


def _fetch_commits_30d(
    client: httpx.Client, org: str, repo: str, headers: dict
) -> int | None:
    """GET /repos/{org}/{repo}/stats/commit_activity → 最近 30 天（4 周）commit 总数。"""
    data = _get_stats_json(client, f"{GITHUB_API}/repos/{org}/{repo}/stats/commit_activity", headers)
    if not data or not isinstance(data, list):
        return None
    # 返回值为最近 52 周数据，取最后 4 项（最近约 30 天）
    recent_weeks = data[-4:] if len(data) >= 4 else data
    return sum(w.get("total", 0) for w in recent_weeks)


def _fetch_contributor_stats_30d(
    client: httpx.Client, org: str, repo: str, headers: dict
) -> tuple[int | None, int | None]:
    """GET /repos/{org}/{repo}/stats/contributors → (active_contributors_30d, new_contributors_30d)。

    active = 最近 4 周内有 commit 的贡献者数
    new = 首次出现在最近 4 周的贡献者数
    """
    data = _get_stats_json(client, f"{GITHUB_API}/repos/{org}/{repo}/stats/contributors", headers)
    if not data or not isinstance(data, list):
        return None, None

    now_ts = int(utc_now().timestamp())
    four_weeks_ago_ts = now_ts - 4 * 7 * 24 * 3600

    active = 0
    new_contributors = 0
    for contributor in data:
        weeks = contributor.get("weeks", [])
        if not weeks:
            continue
        # 最近 4 周是否有 commit
        recent = [w for w in weeks if w.get("w", 0) >= four_weeks_ago_ts]
        if any(w.get("c", 0) > 0 for w in recent):
            active += 1
            # 判断是否是新贡献者：历史 commit 全部在最近 4 周内
            all_commits_before = [w for w in weeks if w.get("w", 0) < four_weeks_ago_ts]
            if not any(w.get("c", 0) > 0 for w in all_commits_before):
                new_contributors += 1

    return active or None, new_contributors or None


def _fetch_prs_merged_30d(
    client: httpx.Client, org: str, repo: str, headers: dict
) -> int | None:
    """GET /repos/{org}/{repo}/pulls?state=closed → 最近 30 天合并的 PR 数。"""
    cutoff = utc_now() - timedelta(days=30)
    url = f"{GITHUB_API}/repos/{org}/{repo}/pulls"
    count = 0

    for page in range(1, 3):  # 最多取 2 页（200 条），通常足够
        data = _get_json(client, url, headers, params={
            "state": "closed", "sort": "updated", "direction": "desc",
            "per_page": 100, "page": page,
        })
        if not data or not isinstance(data, list):
            break
        page_count = 0
        for pr in data:
            merged_at = pr.get("merged_at")
            if not merged_at:
                continue
            # merged_at 格式：2024-01-15T12:00:00Z
            from datetime import datetime
            merged_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            if merged_dt >= cutoff:
                count += 1
                page_count += 1
        # 如果本页没有满 100 条，或最后一条已早于截止日期，停止翻页
        if len(data) < 100:
            break

    return count or None


# ─── 贡献者档案抓取 ────────────────────────────────────────────────────────────


def _enrich_user_profile(
    client: httpx.Client, handle: str, headers: dict
) -> dict:
    """GET /users/{login} → {company, location}。失败时返回空 dict。"""
    data = _get_json(client, f"{GITHUB_API}/users/{handle}", headers)
    if not data or not isinstance(data, dict):
        return {}
    return {
        "company": (data.get("company") or "").strip() or None,
        "location": (data.get("location") or "").strip() or None,
    }


# ─── 主同步函数 ────────────────────────────────────────────────────────────────


def sync_project(db: Session, project: EcosystemProject, token: str | None = None) -> dict:
    """同步单个项目的贡献者数据，并写入时序快照。

    返回 {"created": int, "updated": int, "errors": int}。
    """
    if project.platform != "github":
        logger.info("跳过非 GitHub 项目: %s", project.name)
        return {"created": 0, "updated": 0, "errors": 0}

    headers = _build_headers(token)
    url = f"{GITHUB_API}/repos/{project.org_name}/{project.repo_name}/contributors"

    created = updated = errors = 0
    new_handles: list[str] = []

    try:
        with httpx.Client(timeout=30) as client:
            # ── 1. 同步贡献者列表 ──────────────────────────────────────
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
                    existing_map[handle].last_synced_at = utc_now()
                    updated += 1
                else:
                    db.add(EcosystemContributor(
                        project_id=project.id,
                        github_handle=handle,
                        display_name=item.get("login"),
                        avatar_url=item.get("avatar_url"),
                        commit_count_90d=item.get("contributions"),
                        first_contributed_at=utc_now(),
                        last_synced_at=utc_now(),
                    ))
                    new_handles.append(handle)
                    created += 1

            project.last_synced_at = utc_now()
            db.commit()
            logger.info("项目 %s 贡献者同步完成 — created=%d updated=%d", project.name, created, updated)

            # ── 2. 丰富新贡献者的个人档案（company / location） ────────
            if new_handles:
                # 重新查询，确保对象在当前 session 中
                new_contributors = (
                    db.query(EcosystemContributor)
                    .filter(
                        EcosystemContributor.project_id == project.id,
                        EcosystemContributor.github_handle.in_(new_handles),
                    )
                    .all()
                )
                for contributor in new_contributors:
                    try:
                        profile = _enrich_user_profile(client, contributor.github_handle, headers)
                        if profile.get("company") is not None:
                            contributor.company = profile["company"]
                        if profile.get("location") is not None:
                            contributor.location = profile["location"]
                    except Exception as exc:
                        logger.warning("档案抓取失败 %s: %s", contributor.github_handle, exc)
                db.commit()

            # ── 3. 快照节流判断 ────────────────────────────────────────
            latest_snapshot = (
                db.query(EcosystemSnapshot)
                .filter(EcosystemSnapshot.project_id == project.id)
                .order_by(EcosystemSnapshot.snapshot_at.desc())
                .first()
            )
            if latest_snapshot and latest_snapshot.snapshot_at >= utc_now() - timedelta(
                hours=_SNAPSHOT_MIN_INTERVAL_HOURS
            ):
                logger.info("项目 %s 快照节流，跳过写入", project.name)
                return {"created": created, "updated": updated, "errors": errors}

            # ── 4. 抓取项目级快照数据 ──────────────────────────────────
            stats = _fetch_repo_stats(client, project.org_name, project.repo_name, headers)
            commits_30d = _fetch_commits_30d(client, project.org_name, project.repo_name, headers)
            active_30d, new_30d = _fetch_contributor_stats_30d(
                client, project.org_name, project.repo_name, headers
            )
            prs_30d = _fetch_prs_merged_30d(client, project.org_name, project.repo_name, headers)

            db.add(EcosystemSnapshot(
                project_id=project.id,
                stars=stats["stars"],
                forks=stats["forks"],
                open_issues=stats["open_issues"],
                open_prs=stats["open_prs"],
                commits_30d=commits_30d,
                pr_merged_30d=prs_30d,
                active_contributors_30d=active_30d,
                new_contributors_30d=new_30d,
            ))
            db.commit()
            logger.info("项目 %s 快照已写入", project.name)

    except Exception as exc:
        logger.error("同步项目 %s 失败: %s", project.name, exc)
        errors += 1

    return {"created": created, "updated": updated, "errors": errors}


def sync_all_projects(db: Session, token: str | None = None) -> dict:
    """同步所有活跃项目（向后兼容接口，单线程顺序执行）。

    生产环境推荐使用 sync_worker.sync_projects_due() 的并发版本。
    """
    projects = db.query(EcosystemProject).filter(EcosystemProject.is_active == True).all()  # noqa: E712
    total_created = total_updated = total_errors = 0
    for project in projects:
        result = sync_project(db, project, token)
        total_created += result["created"]
        total_updated += result["updated"]
        total_errors += result["errors"]
    return {"created": total_created, "updated": total_updated, "errors": total_errors}
