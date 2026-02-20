from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Database connection pool configuration
# For SQLite, we need check_same_thread=False
# For PostgreSQL/MySQL, use connection pooling settings
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=settings.DB_ECHO or settings.DEBUG,
    )
else:
    # For PostgreSQL/MySQL with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.DB_ECHO or settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import (  # noqa: F401
        user,
        community,
        audit,
        content,
        channel,
        publish_record,
        password_reset,
        committee,
        meeting,
    )
    Base.metadata.create_all(bind=engine)
    seed_default_admin()


def seed_default_admin():
    """Create the default admin account if no users exist."""
    from app.config import settings
    from app.core.logging import get_logger
    from app.core.security import get_password_hash
    from app.models.user import User

    _logger = get_logger(__name__)
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            default_admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                full_name="Default Administrator",
                is_active=True,
                is_superuser=True,
                is_default_admin=True,
            )
            db.add(default_admin)
            db.commit()
            _logger.info(
                "默认管理员账号已创建",
                extra={"username": settings.DEFAULT_ADMIN_USERNAME},
            )
    finally:
        db.close()
