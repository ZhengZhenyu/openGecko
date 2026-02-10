from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import init_db
from app.api import contents, upload, publish, analytics, auth, communities, committees, channels, meetings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
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
app.include_router(contents.router, prefix="/api/contents", tags=["Contents"])
app.include_router(upload.router, prefix="/api/contents", tags=["Upload"])
app.include_router(publish.router, prefix="/api/publish", tags=["Publish"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(channels.router, prefix="/api/channels", tags=["Channels"])
app.include_router(committees.router, prefix="/api/committees", tags=["Governance"])
app.include_router(meetings.router, prefix="/api/meetings", tags=["Governance"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
