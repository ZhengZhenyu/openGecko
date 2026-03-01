"""采集器调度与并发层。

职责：
- 判断哪些项目到期需要同步（基于 last_synced_at + sync_interval_hours）
- 用 ThreadPoolExecutor 并发触发同步
- 令牌桶限速，确保不超过 GitHub API 配额
- 聚合并返回各线程的同步结果

HTTP 调用由 github_crawler.py 负责；本模块不直接操作 GitHub API。
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, timedelta

from sqlalchemy.orm import Session

from app.core.timezone import utc_now
from app.models.ecosystem import EcosystemProject

logger = logging.getLogger(__name__)


# ─── 令牌桶限速器 ──────────────────────────────────────────────────────────────


class RateLimiter:
    """令牌桶限速器，多线程安全。

    默认 4500 req/hr（为 GitHub 5000/hr 留 10% 余量）。
    """

    def __init__(self, rate_per_hour: int = 4500) -> None:
        self._rate_per_second = rate_per_hour / 3600
        self._tokens = float(rate_per_hour)
        self._max_tokens = float(rate_per_hour)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """消耗一个令牌；若令牌不足则阻塞直到补充。"""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(
                    self._max_tokens,
                    self._tokens + elapsed * self._rate_per_second,
                )
                self._last_refill = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
            # 不持锁等待（避免死锁），稍后重试
            time.sleep(0.1)


# ─── 项目到期判断 ──────────────────────────────────────────────────────────────


def get_projects_due(db: Session) -> list[EcosystemProject]:
    """返回当前需要采集的项目列表。

    条件：
    - auto_sync_enabled = True
    - last_synced_at 为 None（从未同步）OR 距今已超过项目级 sync_interval_hours
      （sync_interval_hours 为 None 时使用 settings.COLLECTOR_SYNC_INTERVAL_HOURS）
    """
    from app.config import settings

    default_interval = settings.COLLECTOR_SYNC_INTERVAL_HOURS
    projects = (
        db.query(EcosystemProject)
        .filter(EcosystemProject.is_active == True)  # noqa: E712
        .filter(EcosystemProject.auto_sync_enabled == True)  # noqa: E712
        .all()
    )

    due = []
    now = utc_now()
    for project in projects:
        if project.last_synced_at is None:
            due.append(project)
            continue
        interval_hours = project.sync_interval_hours or default_interval
        last_synced = project.last_synced_at
        # SQLite 返回 naive datetime；统一加上 UTC 时区再比较
        if last_synced.tzinfo is None:
            last_synced = last_synced.replace(tzinfo=UTC)
        next_sync = last_synced + timedelta(hours=interval_hours)
        if now >= next_sync:
            due.append(project)

    logger.info("到期项目：%d / %d 个", len(due), len(projects))
    return due


# ─── 单项目隔离同步（供 ThreadPoolExecutor 调用） ──────────────────────────────


def _sync_project_isolated(
    project_id: int,
    token: str | None,
    rate_limiter: RateLimiter,
) -> dict:
    """在独立 DB Session 中同步单个项目（线程安全：Session 不跨线程共享）。

    每次 HTTP 调用前消耗一个限速令牌，确保全局 API 速率受控。
    """
    from app.database import SessionLocal
    from app.services.ecosystem.github_crawler import sync_project

    rate_limiter.acquire()  # 等待限速令牌（初次调用几乎无延迟）
    try:
        with SessionLocal() as db:
            project = db.get(EcosystemProject, project_id)
            if project is None:
                logger.warning("项目 %d 不存在，跳过", project_id)
                return {"project_id": project_id, "created": 0, "updated": 0, "errors": 1}
            result = sync_project(db, project, token)
            result["project_id"] = project_id
            return result
    except Exception as exc:
        logger.error("项目 %d 同步异常: %s", project_id, exc)
        return {"project_id": project_id, "created": 0, "updated": 0, "errors": 1}


# ─── 主调度入口 ────────────────────────────────────────────────────────────────


def sync_projects_due(token: str | None = None) -> dict:
    """查找所有到期项目，并发同步，聚合返回结果。

    返回：
        {
            "synced": int,    # 启动同步的项目数
            "created": int,   # 新增贡献者总数
            "updated": int,   # 更新贡献者总数
            "errors": int,    # 出错项目数
        }
    """
    from app.config import settings
    from app.database import SessionLocal

    with SessionLocal() as db:
        due_projects = get_projects_due(db)

    if not due_projects:
        logger.info("无到期项目，本轮跳过")
        return {"synced": 0, "created": 0, "updated": 0, "errors": 0}

    logger.info("开始并发同步 %d 个项目（max_workers=%d）", len(due_projects), settings.COLLECTOR_MAX_WORKERS)
    limiter = RateLimiter()
    project_ids = [p.id for p in due_projects]

    total_created = total_updated = total_errors = 0

    with ThreadPoolExecutor(max_workers=settings.COLLECTOR_MAX_WORKERS) as executor:
        futures = {
            executor.submit(_sync_project_isolated, pid, token, limiter): pid
            for pid in project_ids
        }
        for future in as_completed(futures):
            pid = futures[future]
            try:
                result = future.result()
                total_created += result.get("created", 0)
                total_updated += result.get("updated", 0)
                total_errors += result.get("errors", 0)
            except Exception as exc:
                logger.error("项目 %d future 异常: %s", pid, exc)
                total_errors += 1

    summary = {
        "synced": len(due_projects),
        "created": total_created,
        "updated": total_updated,
        "errors": total_errors,
    }
    logger.info("本轮同步完成: %s", summary)
    return summary
