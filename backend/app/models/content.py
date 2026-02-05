from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SAEnum
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publish_records = relationship("PublishRecord", back_populates="content", cascade="all, delete-orphan")
