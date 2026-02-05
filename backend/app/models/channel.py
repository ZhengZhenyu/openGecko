from sqlalchemy import Column, Integer, String, Boolean, JSON, Enum as SAEnum

from app.database import Base


class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(
        SAEnum("wechat", "hugo", "csdn", "zhihu", name="channel_enum"),
        unique=True,
        nullable=False,
    )
    config = Column(JSON, default=dict)
    enabled = Column(Boolean, default=False)
