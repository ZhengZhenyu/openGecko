from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api import (
    admin,
    analytics,
    auth,
    campaigns,
    channels,
    committees,
    communities,
    community_dashboard,
    contents,
    dashboard,
    ecosystem,
    event_templates,
    events,
    meetings,
    people,
    publish,
    upload,
    wechat_stats,
)
from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import limiter
from app.database import init_db
from app.insights import router as insights_router
from app.services.ecosystem.sync_worker import sync_projects_due
from app.services.issue_sync import run_issue_sync

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)


_scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("openGecko 服务启动", extra={"app": settings.APP_NAME, "debug": settings.DEBUG})
    init_db()

    # 定时任务
    try:
        # 每日 02:00 同步 GitHub Issue 状态
        _scheduler.add_job(
            run_issue_sync,
            trigger="cron",
            hour=2,
            minute=0,
            id="issue_sync",
            replace_existing=True,
        )
        # 生态采集器（嵌入模式）：每小时检查哪些项目到期
        if settings.COLLECTOR_EMBEDDED:
            def _run_ecosystem_sync() -> None:
                sync_projects_due(settings.GITHUB_TOKEN)

            _scheduler.add_job(
                _run_ecosystem_sync,
                trigger="interval",
                hours=1,
                id="ecosystem_sync",
                replace_existing=True,
            )
            logger.info("采集器：嵌入模式（每 1h 检查到期项目）")
        else:
            logger.info("采集器：独立模式（请单独运行 python run_collector.py）")

        _scheduler.start()
        logger.info("APScheduler 已启动")
    except Exception as exc:
        logger.warning("APScheduler 未启动: %s", exc)

    yield

    if _scheduler.running:
        _scheduler.shutdown(wait=False)
    logger.info("openGecko 服务关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# 挂载速率限制器状态和中间件
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(
        "请求参数校验失败",
        extra={"path": str(request.url.path), "errors": str(exc.errors())},
    )

    def make_serializable(obj):
        """递归将不可 JSON 序列化的对象转换为字符串"""
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list | tuple):
            return [make_serializable(i) for i in obj]
        if isinstance(obj, Exception):
            return str(obj)
        # 直接类型判断替代 json.dumps try/except，避免每次序列化对象带来开销
        if isinstance(obj, str | int | float | bool) or obj is None:
            return obj
        return str(obj)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": make_serializable(exc.errors()),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(
        "数据库异常",
        extra={"path": str(request.url.path), "error": str(exc)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(
        "未预期异常",
        extra={"path": str(request.url.path), "error": str(exc)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc) if settings.DEBUG else "Internal server error",
        },
    )


# Serve uploaded files — only in local storage mode.
# When STORAGE_BACKEND=s3, nginx proxies /uploads/ directly to MinIO.
if settings.STORAGE_BACKEND == "local":
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# Register API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(communities.router, prefix="/api/communities", tags=["Communities"])
app.include_router(dashboard.router, prefix="/api/users/me", tags=["Dashboard"])
app.include_router(contents.router, prefix="/api/contents", tags=["Contents"])
app.include_router(upload.router, prefix="/api/contents", tags=["Upload"])
app.include_router(publish.router, prefix="/api/publish", tags=["Publish"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(channels.router, prefix="/api/channels", tags=["Channels"])
app.include_router(committees.router, prefix="/api/committees", tags=["Governance"])
app.include_router(meetings.router, prefix="/api/meetings", tags=["Governance"])
app.include_router(community_dashboard.router, prefix="/api/communities", tags=["Community Dashboard"])
app.include_router(wechat_stats.router, prefix="/api/wechat-stats", tags=["WeChat Statistics"])
if settings.ENABLE_INSIGHTS_MODULE:
    app.include_router(people.router, prefix="/api/people", tags=["People"])
    app.include_router(ecosystem.router, prefix="/api/ecosystem", tags=["Ecosystem"])
    app.include_router(insights_router.router, prefix="/api/insights", tags=["Insights"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(event_templates.router, prefix="/api/event-templates", tags=["Event Templates"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/config/features")
def get_features():
    """返回各可选功能模块的开关状态（无需认证，前端启动时拉取）"""
    return {"insights_module": settings.ENABLE_INSIGHTS_MODULE}
