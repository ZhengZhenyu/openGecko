from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class EcosystemProject(Base):
    __tablename__ = "ecosystem_projects"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    platform = Column(String(30), nullable=False)   # github / gitee / gitcode
    org_name = Column(String(200), nullable=False)
    repo_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)
    added_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contributors = relationship(
        "EcosystemContributor",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class EcosystemContributor(Base):
    __tablename__ = "ecosystem_contributors"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("ecosystem_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    github_handle = Column(String(100), nullable=False, index=True)
    display_name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(String(50), nullable=True)
    commit_count_90d = Column(Integer, nullable=True)
    pr_count_90d = Column(Integer, nullable=True)
    star_count = Column(Integer, nullable=True)
    followers = Column(Integer, nullable=True)
    # 关联到人脉库
    person_id = Column(Integer, ForeignKey("person_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("EcosystemProject", back_populates="contributors")
    person = relationship("PersonProfile")
