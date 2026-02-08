#!/usr/bin/env python3
"""
Initialize old database schema for testing migration.
This creates the pre-Phase1 database structure that the migration expects.
"""

import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


# Old Content model (before Phase 1)
class OldContent(Base):
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


# Old ChannelConfig model (before Phase 1)
class OldChannelConfig(Base):
    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(
        SAEnum("wechat", "hugo", "csdn", "zhihu", name="channel_enum"),
        unique=True,
        nullable=False,
    )
    config = Column(JSON, default=dict)
    enabled = Column(Boolean, default=False)


# Old PublishRecord model
class OldPublishRecord(Base):
    __tablename__ = "publish_records"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, nullable=False)
    channel = Column(
        SAEnum("wechat", "hugo", "csdn", "zhihu", name="publish_channel_enum"),
        nullable=False,
    )
    status = Column(
        SAEnum("pending", "success", "failed", name="publish_status_enum"),
        default="pending",
    )
    platform_id = Column(String(200), nullable=True)
    platform_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_old_schema(database_url: str = "sqlite:///./content_hub.db"):
    """Initialize the old schema before Phase 1."""
    # If the input is just a filename (not a full URL), convert to SQLite URL
    if not database_url.startswith("sqlite:"):
        database_url = f"sqlite:///./{database_url}"

    print(f"Creating old schema in {database_url}")

    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ Old schema created successfully")
    print("Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    database_url = sys.argv[1] if len(sys.argv) > 1 else "sqlite:///./content_hub.db"
    init_old_schema(database_url)
