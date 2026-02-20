"""
速率限制模块

使用 slowapi 实现基于 IP 的速率限制。
Limiter 实例在此处创建，在 main.py 中挂载到应用，
在各路由文件中通过装饰器使用。
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# 全局 Limiter 实例，基于客户端 IP 进行限制
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)
