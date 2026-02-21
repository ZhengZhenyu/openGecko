"""
结构化日志模块

使用 python-json-logger 将日志输出为 JSON 格式，方便在生产环境中
通过日志聚合工具（如 ELK、Loki）进行查询和监控。

开发环境（DEBUG=true）时使用更易读的格式；
生产环境（DEBUG=false）时输出 JSON 格式以便机器解析。
"""

import logging
import sys

from app.config import settings


def setup_logging(level: str | None = None) -> None:
    """
    初始化应用程序日志系统。

    - DEBUG 模式：使用易读的文本格式，级别 DEBUG
    - 生产模式：使用 JSON 格式，级别 INFO
    """
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")

    # 清除已有的 handler，避免重复
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.DEBUG:
        # 开发环境：人类可读格式
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # 生产环境：JSON 格式
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        except ImportError:
            # 如果 python-json-logger 未安装，回退到文本格式
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # 降低第三方库的日志级别，减少噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DB_ECHO else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger。

    用法示例：
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("操作成功", extra={"user_id": 1, "action": "login"})
    """
    return logging.getLogger(name)
