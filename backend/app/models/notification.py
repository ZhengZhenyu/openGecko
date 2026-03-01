from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base


class NotificationType(str, Enum):
    TASK_ASSIGNED = "task_assigned"        # 活动任务被指派给当前用户
    MEETING_REMINDER = "meeting_reminder"  # 会议即将开始提醒


class Notification(Base):
    """站内通知记录。每条通知属于特定用户，可选关联资源（event_task / meeting）。"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type = Column(String(40), nullable=False)           # NotificationType 值
    title = Column(String(200), nullable=False)
    body = Column(String(500), nullable=True)

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # 可选：跳转资源
    resource_type = Column(String(40), nullable=True)   # "event_task" | "meeting"
    resource_id = Column(Integer, nullable=True)

    # 关系
    user = relationship("User", back_populates="notifications")
