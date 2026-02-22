"""GitHub / Gitee / GitCode Issue 状态同步服务。

每日定时（APScheduler BackgroundScheduler）调用 run_issue_sync()，
对所有 IssueLink 记录发起 API 请求更新 issue_status 字段。
"""

import asyncio
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.event import IssueLink

logger = logging.getLogger(__name__)

# GitHub API base
GITHUB_API = "https://api.github.com"


def _fetch_github_issue_status_sync(repo: str, issue_number: int, token: Optional[str] = None) -> Optional[str]:
    """同步方式获取 GitHub Issue 状态（open / closed）。"""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{GITHUB_API}/repos/{repo}/issues/{issue_number}"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json().get("state", "open")
            logger.warning("GitHub API %s → %s", url, resp.status_code)
    except Exception as exc:
        logger.error("Failed to fetch GitHub issue %s#%s: %s", repo, issue_number, exc)
    return None


def run_issue_sync(github_token: Optional[str] = None) -> dict:
    """同步入口：遍历所有 IssueLink，刷新 issue_status。

    只处理 platform='github' 的记录；其他平台预留扩展。
    由 APScheduler BackgroundScheduler 在后台线程中调用。
    返回 {"updated": int, "skipped": int, "errors": int}。
    """
    db: Session = SessionLocal()
    updated = skipped = errors = 0
    try:
        links = db.query(IssueLink).filter(IssueLink.platform == "github").all()
        for link in links:
            new_status = _fetch_github_issue_status_sync(link.repo, link.issue_number, github_token)
            if new_status is None:
                errors += 1
                continue
            if new_status != link.issue_status:
                link.issue_status = new_status
                updated += 1
            else:
                skipped += 1
        db.commit()
    except Exception as exc:
        logger.error("Issue sync failed: %s", exc)
        db.rollback()
    finally:
        db.close()

    logger.info("Issue sync done — updated=%s skipped=%s errors=%s", updated, skipped, errors)
    return {"updated": updated, "skipped": skipped, "errors": errors}
