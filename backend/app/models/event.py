from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base

# 活动 ↔ 社区 多对多关联表
event_communities_table = Table(
    "event_communities",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("community_id", Integer, ForeignKey("communities.id", ondelete="CASCADE"), primary_key=True),
)


class EventTemplate(Base):
    """活动 SOP 模板"""
    __tablename__ = "event_templates"

    id = Column(Integer, primary_key=True)
    community_id = Column(
        Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name = Column(String(200), nullable=False)
    event_type = Column(
        SAEnum("online", "offline", "hybrid", name="event_type_enum"),
        nullable=False,
    )
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    checklist_items = relationship(
        "ChecklistTemplateItem", back_populates="template", cascade="all, delete-orphan"
    )
    events = relationship("Event", back_populates="template")


class ChecklistTemplateItem(Base):
    """SOP 模板检查项"""
    __tablename__ = "checklist_template_items"

    id = Column(Integer, primary_key=True)
    template_id = Column(
        Integer, ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase = Column(
        SAEnum("pre", "during", "post", name="checklist_phase_enum"), nullable=False
    )
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)

    template = relationship("EventTemplate", back_populates="checklist_items")


class Event(Base):
    """活动"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    community_id = Column(
        Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title = Column(String(300), nullable=False)
    event_type = Column(
        SAEnum("online", "offline", "hybrid", name="event_type_enum"),
        nullable=False,
        default="offline",
    )
    template_id = Column(
        Integer, ForeignKey("event_templates.id", ondelete="SET NULL"), nullable=True
    )
    status = Column(
        SAEnum("planning", "ongoing", "completed", name="event_status_enum"),
        default="planning",
    )
    planned_at = Column(DateTime(timezone=True), nullable=True)
    duration_hours = Column(Float, nullable=True)
    location = Column(String(300), nullable=True)
    online_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # 活动结果内嵌字段
    attendee_count = Column(Integer, nullable=True)
    online_count = Column(Integer, nullable=True)
    offline_count = Column(Integer, nullable=True)
    registration_count = Column(Integer, nullable=True)
    result_summary = Column(Text, nullable=True)
    media_urls = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    template = relationship("EventTemplate", back_populates="events")
    communities = relationship(
        "Community", secondary="event_communities", lazy="selectin"
    )
    checklist_items = relationship(
        "ChecklistItem", back_populates="event", cascade="all, delete-orphan"
    )
    personnel = relationship(
        "EventPersonnel", back_populates="event", cascade="all, delete-orphan"
    )
    attendees = relationship(
        "EventAttendee", back_populates="event", cascade="all, delete-orphan"
    )
    feedback_items = relationship(
        "FeedbackItem", back_populates="event", cascade="all, delete-orphan"
    )
    tasks = relationship("EventTask", back_populates="event", cascade="all, delete-orphan")


class ChecklistItem(Base):
    """活动实例检查项"""
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase = Column(
        SAEnum("pre", "during", "post", name="checklist_item_phase_enum"), nullable=False
    )
    title = Column(String(300), nullable=False)
    status = Column(
        SAEnum("pending", "done", "skipped", name="checklist_status_enum"), default="pending"
    )
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    order = Column(Integer, default=0)

    event = relationship("Event", back_populates="checklist_items")


class EventPersonnel(Base):
    """活动人员安排"""
    __tablename__ = "event_personnel"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(50), nullable=False)
    role_label = Column(String(100), nullable=True)
    assignee_type = Column(
        SAEnum("internal", "external", name="personnel_assignee_enum"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    person_id = Column(
        Integer, ForeignKey("person_profiles.id", ondelete="SET NULL"), nullable=True
    )
    confirmed = Column(
        SAEnum("pending", "confirmed", "declined", name="personnel_confirm_enum"),
        default="pending",
    )
    time_slot = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    order = Column(Integer, default=0)

    event = relationship("Event", back_populates="personnel")


class EventAttendee(Base):
    """活动签到记录"""
    __tablename__ = "event_attendees"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id = Column(
        Integer, ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checked_in = Column(Boolean, default=False)
    role_at_event = Column(String(100), nullable=True)
    source = Column(
        SAEnum("manual", "excel_import", name="attendee_source_enum"), default="manual"
    )

    event = relationship("Event", back_populates="attendees")
    person = relationship("PersonProfile", back_populates="event_attendances")


class FeedbackItem(Base):
    """活动反馈/问题记录"""
    __tablename__ = "feedback_items"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    category = Column(String(50), default="question")
    raised_by = Column(String(200), nullable=True)
    raised_by_person_id = Column(
        Integer, ForeignKey("person_profiles.id", ondelete="SET NULL"), nullable=True
    )
    status = Column(
        SAEnum("open", "in_progress", "closed", name="feedback_status_enum"), default="open"
    )
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    event = relationship("Event", back_populates="feedback_items")
    issue_links = relationship("IssueLink", back_populates="feedback", cascade="all, delete-orphan")


class IssueLink(Base):
    """反馈问题关联的 Issue/PR"""
    __tablename__ = "issue_links"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(
        Integer, ForeignKey("feedback_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform = Column(
        SAEnum("github", "gitcode", "gitee", name="issue_platform_enum"), nullable=False
    )
    repo = Column(String(200), nullable=False)
    issue_number = Column(Integer, nullable=False)
    issue_url = Column(String(500), nullable=False)
    issue_type = Column(
        SAEnum("issue", "pr", name="issue_type_enum"), default="issue"
    )
    issue_status = Column(
        SAEnum("open", "closed", name="issue_status_enum"), default="open"
    )
    linked_at = Column(DateTime(timezone=True), default=utc_now)
    linked_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    feedback = relationship("FeedbackItem", back_populates="issue_links")


class EventTask(Base):
    """活动任务/里程碑（甘特图数据）"""
    __tablename__ = "event_tasks"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(300), nullable=False)
    task_type = Column(
        SAEnum("task", "milestone", name="task_type_enum"), default="task"
    )
    phase = Column(
        SAEnum("pre", "during", "post", name="task_phase_enum"), default="pre"
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    progress = Column(Integer, default=0)
    status = Column(
        SAEnum("not_started", "in_progress", "completed", "blocked", name="task_status_enum"),
        default="not_started",
    )
    depends_on = Column(JSON, default=list)   # list[int] task IDs
    parent_task_id = Column(
        Integer, ForeignKey("event_tasks.id", ondelete="SET NULL"), nullable=True
    )
    order = Column(Integer, default=0)

    event = relationship("Event", back_populates="tasks")
