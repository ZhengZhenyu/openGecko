from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=False)          # promotion / care / invitation / survey
    status = Column(String(50), nullable=False, default="draft")  # draft / active / completed / archived
    target_count = Column(Integer, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")
    activities = relationship("CampaignActivity", back_populates="campaign", cascade="all, delete-orphan")
    tasks = relationship("CampaignTask", back_populates="campaign", cascade="all, delete-orphan")


class CampaignContact(Base):
    __tablename__ = "campaign_contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(Integer, ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")   # pending/contacted/responded/converted/declined
    channel = Column(String(50), nullable=True)                       # email/wechat/phone/in_person/other
    added_by = Column(String(50), nullable=False, default="manual")  # manual/event_import/ecosystem_import/csv_import
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    campaign = relationship("Campaign", back_populates="contacts")
    person = relationship("PersonProfile")


class CampaignActivity(Base):
    __tablename__ = "campaign_activities"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(Integer, ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # sent_email/made_call/sent_wechat/in_person_meeting/got_reply/note
    content = Column(Text, nullable=True)
    outcome = Column(String(300), nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    campaign = relationship("Campaign", back_populates="activities")
    person = relationship("PersonProfile")


class CampaignTask(Base):
    """运营活动任务（任务规划，联动个人工作台）"""
    __tablename__ = "campaign_tasks"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(50), nullable=False, default="not_started"
    )  # not_started / in_progress / completed / blocked
    priority = Column(String(20), nullable=False, default="medium")  # low / medium / high
    assignee_ids = Column(JSON, default=list)   # list[int] user IDs
    deadline = Column(Date, nullable=True)
    created_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    campaign = relationship("Campaign", back_populates="tasks")
