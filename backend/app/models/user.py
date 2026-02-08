from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


# Association table for many-to-many relationship between users and communities
community_users = Table(
    "community_users",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("community_id", Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(50), default="member"),  # Reserved for future RBAC
    Column("joined_at", DateTime, default=datetime.utcnow),
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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    communities = relationship(
        "Community",
        secondary=community_users,
        back_populates="members",
    )
    created_contents = relationship("Content", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
