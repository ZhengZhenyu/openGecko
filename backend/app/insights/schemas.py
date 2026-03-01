"""生态情报模块数据契约（Pydantic schemas）。

这是消费方与分析层之间的接口定义，先于 Analyzer 实现完成，
保证前端和其他模块可按此契约并行开发。
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel  # noqa: I001 (pydantic is third-party, sorted after stdlib)

# ─── 趋势分析 ────────────────────────────────────────────────────────────────


class MomentumLevel(str, Enum):
    ACCELERATING = "accelerating"       # 加速期：多指标环比增长
    GROWING = "growing"                 # 增长期：指标稳步向好
    STABLE = "stable"                   # 成熟期：高绝对值但增速放缓
    DECLINING = "declining"             # 衰退期：贡献者净流失
    INSUFFICIENT = "insufficient_data"  # 快照数 < 2，无法计算趋势


class ProjectTrend(BaseModel):
    project_id: int
    project_name: str
    momentum: MomentumLevel
    velocity_score: float               # 0–100 综合增速评分
    star_growth_30d: int | None         # 最近一个快照周期的 star 增量
    contributor_growth_30d: int | None  # 贡献者净增量
    active_contributors_30d: int | None
    pr_merged_30d: int | None
    snapshot_count: int                 # 可用快照数（0 表示数据不足）
    latest_snapshot_at: datetime | None


# ─── 关键人物识别 ─────────────────────────────────────────────────────────────


class InfluenceType(str, Enum):
    MAINTAINER = "maintainer"      # role="maintainer"，有合并 PR 权限
    BRIDGE = "bridge"              # 跨 ≥2 个追踪项目活跃
    RISING_STAR = "rising_star"    # 近 90 天首次贡献且 commit_count_90d ≥ 5
    REVIEWER = "reviewer"          # review_count_90d ≥ 5
    CONTRIBUTOR = "contributor"    # 普通贡献者（兜底类型）


class KeyPerson(BaseModel):
    github_handle: str
    display_name: str | None
    avatar_url: str | None
    influence_types: list[InfluenceType]
    influence_score: float          # 0–100 加权综合评分
    cross_project_count: int        # 在追踪项目中活跃的项目数
    commit_count_90d: int | None
    pr_count_90d: int | None
    review_count_90d: int | None
    company: str | None
    person_profile_id: int | None   # 已关联 PersonProfile 的 ID
    project_ids: list[int]          # 活跃的 project_id 列表


# ─── 企业图谱 ─────────────────────────────────────────────────────────────────


class ProjectPresence(BaseModel):
    project_id: int
    project_name: str
    contributor_count: int
    has_maintainer: bool
    commit_share: float             # 该公司 commit 占项目总 commit_count_90d 的比例（0–1）


class CorporateLandscape(BaseModel):
    company: str
    project_count: int              # 出现在几个追踪项目中
    strategic_score: float          # 0–100，跨项目广度评分
    has_maintainer: bool            # 在任一项目有 maintainer 角色
    total_contributors: int
    projects: list[ProjectPresence]
