from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, JSON,
    ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Committee(Base):
    """委员会/理事会"""
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, default="")

    is_active = Column(Boolean, default=True)

    meeting_frequency = Column(String(50), nullable=True)  # monthly, quarterly, yearly
    notification_email = Column(String(200), nullable=True)
    notification_wechat = Column(String(100), nullable=True)

    established_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    community = relationship("Community", back_populates="committees")
    members = relationship(
        "CommitteeMember",
        back_populates="committee",
        cascade="all, delete-orphan",
    )
    meetings = relationship(
        "Meeting",
        back_populates="committee",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("community_id", "slug", name="uq_committee_community_slug"),
    )


class CommitteeMember(Base):
    """委员会成员"""
    __tablename__ = "committee_members"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(
        Integer,
        ForeignKey("committees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    wechat = Column(String(100), nullable=True)
    organization = Column(String(200), nullable=True)

    # 角色标签（中文，可多选，JSON数组）
    # 可选值: ["主席", "副主席", "委员", "常务委员"]
    roles = Column(JSON, default=list)

    term_start = Column(Date, nullable=True)
    term_end = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    joined_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    committee = relationship("Committee", back_populates="members")
