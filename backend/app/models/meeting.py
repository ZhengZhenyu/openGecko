from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, JSON,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Meeting(Base):
    """理事会会议"""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(
        Integer,
        ForeignKey("committees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    community_id = Column(
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration = Column(Integer, default=120)  # 持续时长（分钟）

    location_type = Column(String(50), nullable=True)  # online / offline / hybrid
    location = Column(String(500), nullable=True)

    status = Column(String(50), default="scheduled", index=True)
    # 可选值: scheduled, in_progress, completed, cancelled

    agenda = Column(Text, nullable=True)       # 会议议程（Markdown）
    minutes = Column(Text, nullable=True)      # 会议纪要（Markdown）
    attachments = Column(JSON, default=list)   # 附件列表 [{name, url}]

    reminder_sent = Column(Boolean, default=False)
    reminder_before_hours = Column(Integer, default=24)

    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    committee = relationship("Committee", back_populates="meetings")
    community = relationship("Community")
    created_by = relationship("User")


class MeetingReminder(Base):
    """会议提醒记录"""
    __tablename__ = "meeting_reminders"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(
        Integer,
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reminder_type = Column(String(50), nullable=False)
    # 可选值: preparation, one_week, three_days, one_day, two_hours

    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    notification_channels = Column(JSON, default=list)  # ['email', 'wechat']

    status = Column(String(50), default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting")

    __table_args__ = (
        Index("idx_reminder_scheduled_status", "scheduled_at", "status"),
    )
