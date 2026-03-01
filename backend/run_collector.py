#!/usr/bin/env python
"""独立采集器进程。

可不依赖 FastAPI 单独运行，也可容器化部署为独立服务。
使用方式：
  python run_collector.py            # 持续运行（按 COLLECTOR_CHECK_INTERVAL_SECONDS 循环）
  python run_collector.py --once     # 立即执行一次后退出（适合 CI / k8s Job / cron）

环境变量：
  GITHUB_TOKEN              GitHub PAT（可选，不填则受 60 req/h 匿名限速）
  COLLECTOR_EMBEDDED        设为 false 表示采用独立模式（FastAPI 侧不启动调度）
  COLLECTOR_MAX_WORKERS     并发线程数（默认 4）
  COLLECTOR_CHECK_INTERVAL_SECONDS  循环检查间隔（默认 3600 秒）
"""

import argparse
import logging
import os
import sys
import time

# 确保从 backend/ 目录运行时 app 包可被找到
sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings
from app.core.logging import setup_logging
from app.database import init_db
from app.services.ecosystem.sync_worker import sync_projects_due

setup_logging()
logger = logging.getLogger("collector")


def main() -> None:
    parser = argparse.ArgumentParser(description="openGecko 生态采集器")
    parser.add_argument(
        "--once",
        action="store_true",
        help="立即执行一次采集后退出（默认：持续运行）",
    )
    args = parser.parse_args()

    logger.info("采集器启动 — token=%s once=%s", "已配置" if settings.GITHUB_TOKEN else "未配置", args.once)
    init_db()

    if args.once:
        result = sync_projects_due(settings.GITHUB_TOKEN)
        logger.info("采集完成: %s", result)
        return

    logger.info(
        "进入持续运行模式，每 %d 秒检查一次到期项目",
        settings.COLLECTOR_CHECK_INTERVAL_SECONDS,
    )
    while True:
        try:
            result = sync_projects_due(settings.GITHUB_TOKEN)
            logger.info("本轮完成: %s", result)
        except Exception as exc:
            logger.error("本轮采集异常: %s", exc)
        time.sleep(settings.COLLECTOR_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
