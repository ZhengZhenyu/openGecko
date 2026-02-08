from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., create_content, publish_to_wechat, update_status
    resource_type = Column(String(50), nullable=False)  # e.g., content, channel_config, community
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    details = Column(JSON, default=dict)  # Additional details about the action
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    community = relationship("Community", back_populates="audit_logs")
