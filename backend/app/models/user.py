from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base

# Association table for many-to-many relationship between users and communities
community_users = Table(
    "community_users",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("community_id", Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(50), default="user"),  # 'admin', 'user' (superuser is global)
    Column("joined_at", DateTime(timezone=True), default=utc_now),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(200), default="")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # Superuser can access all communities
    is_default_admin = Column(Boolean, default=False)  # Marks the seeded default admin account
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    communities = relationship(
        "Community",
        secondary=community_users,
        back_populates="members",
    )
    created_contents = relationship("Content", foreign_keys="Content.created_by_user_id", back_populates="creator")
    owned_contents = relationship("Content", foreign_keys="Content.owner_id", back_populates="owner")
    collaborated_contents = relationship(
        "Content",
        secondary="content_collaborators",
        back_populates="collaborators",
    )
    assigned_contents = relationship(
        "Content",
        secondary="content_assignees",
        primaryjoin="User.id == content_assignees.c.user_id",
        secondaryjoin="Content.id == content_assignees.c.content_id",
        back_populates="assignees",
    )
    assigned_meetings = relationship(
        "Meeting",
        secondary="meeting_assignees",
        primaryjoin="User.id == meeting_assignees.c.user_id",
        secondaryjoin="Meeting.id == meeting_assignees.c.meeting_id",
        back_populates="assignees",
    )
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
