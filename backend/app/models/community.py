from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.user import community_users


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly identifier
    description = Column(Text, default="")
    logo_url = Column(String(500), nullable=True)
    settings = Column(JSON, default=dict)  # Community-level settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship(
        "User",
        secondary=community_users,
        back_populates="communities",
    )
    contents = relationship("Content", back_populates="community", cascade="all, delete-orphan")
    channel_configs = relationship("ChannelConfig", back_populates="community", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="community", cascade="all, delete-orphan")
