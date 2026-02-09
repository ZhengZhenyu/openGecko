from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=settings.DEBUG,
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
    """Create the default admin account and default community if no users exist."""
    from app.config import settings
    from app.core.security import get_password_hash
    from app.models.user import User, community_users
    from app.models.community import Community
    from sqlalchemy import insert

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            # Create default admin
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

            # Create default community if none exists
            community_count = db.query(Community).count()
            if community_count == 0:
                default_community = Community(
                    name="Default Community",
                    slug="default",
                    description="Default community for content management",
                    is_active=True,
                )
                db.add(default_community)
                db.flush()  # Get IDs assigned
                
                # Add admin to community with 'admin' role
                stmt = insert(community_users).values(
                    user_id=default_admin.id,
                    community_id=default_community.id,
                    role='admin'
                )
                db.execute(stmt)

            db.commit()
            print(f"[INFO] Default admin account created: {settings.DEFAULT_ADMIN_USERNAME}")
            if community_count == 0:
                print("[INFO] Default community created: Default Community")
    finally:
        db.close()
