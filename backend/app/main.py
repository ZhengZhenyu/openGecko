from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import limiter
from app.database import init_db
from app.api import contents, upload, publish, analytics, auth, communities, committees, channels, meetings, dashboard, community_dashboard

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("openGecko 服务启动", extra={"app": settings.APP_NAME, "debug": settings.DEBUG})
    init_db()
    yield
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
        if isinstance(obj, (list, tuple)):
            return [make_serializable(i) for i in obj]
        return obj

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


# Serve uploaded files
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


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
