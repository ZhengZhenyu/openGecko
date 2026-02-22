from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base


class PersonProfile(Base):
    """社区人脉档案（独立于系统 User，覆盖外部参与者）"""
    __tablename__ = "person_profiles"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String(200), nullable=False, index=True)
    avatar_url = Column(String(500), nullable=True)
    github_handle = Column(String(100), nullable=True, unique=True, index=True)
    gitcode_handle = Column(String(100), nullable=True, unique=True, index=True)
    email = Column(String(200), nullable=True, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True, index=True)
    location = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    source = Column(
        SAEnum("manual", "event_import", "ecosystem_import", name="person_source_enum"),
        nullable=False,
        default="manual",
    )
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    community_roles = relationship("CommunityRole", back_populates="person", cascade="all, delete-orphan")
    event_attendances = relationship("EventAttendee", back_populates="person")


class CommunityRole(Base):
    """人脉的社区身份记录"""
    __tablename__ = "community_roles"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(
        Integer,
        ForeignKey("person_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    community_name = Column(String(200), nullable=False)
    project_url = Column(String(500), nullable=True)
    role = Column(String(100), nullable=False)
    role_label = Column(String(100), nullable=True)
    is_current = Column(Boolean, default=True)
    started_at = Column(Date, nullable=True)
    ended_at = Column(Date, nullable=True)
    source_url = Column(String(500), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    person = relationship("PersonProfile", back_populates="community_roles")
