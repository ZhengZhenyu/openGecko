from sqlalchemy import Column, Integer, String, Boolean, JSON, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class ChannelConfig(Base):
    __tablename__ = "channel_configs"
    __table_args__ = (
        UniqueConstraint("community_id", "channel", name="uq_community_channel"),
    )

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(
        SAEnum("wechat", "hugo", "csdn", "zhihu", name="channel_enum"),
        nullable=False,
    )
    # Multi-tenancy field
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    config = Column(JSON, default=dict)
    enabled = Column(Boolean, default=False)

    # Relationships
    community = relationship("Community", back_populates="channel_configs")
