from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base
from app.models.user import community_users


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly identifier
    description = Column(Text, default="")
    url = Column(String(500), nullable=True)  # 社区官网或项目仓库地址
    logo_url = Column(String(500), nullable=True)
    settings = Column(JSON, default=dict)  # Community-level settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    members = relationship(
        "User",
        secondary=community_users,
        back_populates="communities",
    )
    contents = relationship("Content", back_populates="community", cascade="all, delete-orphan")
    linked_contents = relationship(
        "Content",
        secondary="content_communities",
        back_populates="communities",
    )
    channel_configs = relationship("ChannelConfig", back_populates="community", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="community", cascade="all, delete-orphan")
    committees = relationship("Committee", back_populates="community", cascade="all, delete-orphan")
