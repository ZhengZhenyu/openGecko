from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base


class PublishRecord(Base):
    __tablename__ = "publish_records"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    channel = Column(
        SAEnum("wechat", "hugo", "csdn", "zhihu", name="pub_channel_enum"),
        nullable=False,
    )
    status = Column(
        SAEnum("pending", "draft", "published", "failed", name="pub_status_enum"),
        default="pending",
    )
    platform_article_id = Column(String(200), nullable=True)
    platform_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("Content", back_populates="publish_records")
    analytics = relationship("ContentAnalytics", back_populates="publish_record", cascade="all, delete-orphan")


class ContentAnalytics(Base):
    __tablename__ = "content_analytics"

    id = Column(Integer, primary_key=True, index=True)
    publish_record_id = Column(Integer, ForeignKey("publish_records.id"), nullable=False)
    read_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    collected_at = Column(DateTime, default=datetime.utcnow)

    publish_record = relationship("PublishRecord", back_populates="analytics")
