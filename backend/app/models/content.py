from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base

# Association table for content collaborators
content_collaborators = Table(
    "content_collaborators",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("content_id", Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("added_at", DateTime, default=datetime.utcnow),
)


# Association table for content assignees (责任人)
content_assignees = Table(
    "content_assignees",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("content_id", Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
    Column("assigned_by_user_id", Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
)


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content_markdown = Column(Text, default="")
    content_html = Column(Text, default="")
    source_type = Column(
        SAEnum("contribution", "release_note", "event_summary", name="source_type_enum"),
        default="contribution",
    )
    source_file = Column(String(500), nullable=True)
    author = Column(String(200), default="")
    tags = Column(JSON, default=list)
    category = Column(String(100), default="")
    cover_image = Column(String(500), nullable=True)
    status = Column(
        SAEnum("draft", "reviewing", "approved", "published", name="status_enum"),
        default="draft",
    )
    # Work status (工作状态): planning, in_progress, completed
    work_status = Column(String(50), default="planning", index=True)
    # Multi-tenancy fields
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # Ownership field (defaults to creator)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # Calendar/scheduling field
    scheduled_publish_at = Column(DateTime, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publish_records = relationship("PublishRecord", back_populates="content", cascade="all, delete-orphan")
    community = relationship("Community", back_populates="contents")
    creator = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_contents")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_contents")
    collaborators = relationship(
        "User",
        secondary="content_collaborators",
        back_populates="collaborated_contents",
    )
    assignees = relationship(
        "User",
        secondary="content_assignees",
        primaryjoin="Content.id == content_assignees.c.content_id",
        secondaryjoin="User.id == content_assignees.c.user_id",
        back_populates="assigned_contents",
    )
