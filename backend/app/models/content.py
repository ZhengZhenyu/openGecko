from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


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
    # Multi-tenancy fields
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # Calendar/scheduling field
    scheduled_publish_at = Column(DateTime, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publish_records = relationship("PublishRecord", back_populates="content", cascade="all, delete-orphan")
    community = relationship("Community", back_populates="contents")
    creator = relationship("User", back_populates="created_contents")
