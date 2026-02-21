from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base

# Association table for meeting assignees (责任人)
meeting_assignees = Table(
    "meeting_assignees",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("meeting_id", Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
    Column("assigned_by_user_id", Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
)


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

    # Work status (工作状态): planning, in_progress, completed
    work_status = Column(String(50), default="planning", index=True)

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
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    assignees = relationship(
        "User",
        secondary="meeting_assignees",
        primaryjoin="Meeting.id == meeting_assignees.c.meeting_id",
        secondaryjoin="User.id == meeting_assignees.c.user_id",
        back_populates="assigned_meetings",
    )
    participants = relationship(
        "MeetingParticipant",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )


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


class MeetingParticipant(Base):
    """会议与会人"""
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(
        Integer,
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    source = Column(String(50), default="manual")  # manual / committee_import
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="participants")

    __table_args__ = (
        UniqueConstraint("meeting_id", "email", name="uq_meeting_participant_email"),
    )
