from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base


class EcosystemProject(Base):
    __tablename__ = "ecosystem_projects"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    platform = Column(String(30), nullable=False)   # github / gitee / gitcode
    org_name = Column(String(200), nullable=False)
    repo_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    added_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    # 采集配置（为独立 collector 服务预留）
    auto_sync_enabled = Column(Boolean, default=True, nullable=False)
    # null 表示使用全局默认值（COLLECTOR_SYNC_INTERVAL_HOURS）
    sync_interval_hours = Column(Integer, nullable=True)

    contributors = relationship(
        "EcosystemContributor",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    snapshots = relationship(
        "EcosystemSnapshot",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="EcosystemSnapshot.snapshot_at",
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
    last_synced_at = Column(DateTime(timezone=True), default=utc_now)
    # 情报分析字段（由采集器填充，初始为 null）
    review_count_90d = Column(Integer, nullable=True)           # code review 次数
    company = Column(String(200), nullable=True)                # GitHub profile company
    location = Column(String(200), nullable=True)               # GitHub profile location
    first_contributed_at = Column(DateTime(timezone=True), nullable=True)  # 首次贡献时间

    project = relationship("EcosystemProject", back_populates="contributors")
    person = relationship("PersonProfile")


class EcosystemSnapshot(Base):
    """项目时序快照，每次采集写入一条，用于趋势动量分析。"""

    __tablename__ = "ecosystem_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("ecosystem_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    # 平台指标
    stars = Column(Integer, nullable=True)
    forks = Column(Integer, nullable=True)
    open_issues = Column(Integer, nullable=True)
    open_prs = Column(Integer, nullable=True)

    # 活跃度指标（30 天窗口）
    commits_30d = Column(Integer, nullable=True)
    pr_merged_30d = Column(Integer, nullable=True)
    active_contributors_30d = Column(Integer, nullable=True)
    new_contributors_30d = Column(Integer, nullable=True)

    project = relationship("EcosystemProject", back_populates="snapshots")
