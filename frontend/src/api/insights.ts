import apiClient from './index'

// ─── 趋势分析 ────────────────────────────────────────────────────────────────

export type MomentumLevel =
  | 'accelerating'
  | 'growing'
  | 'stable'
  | 'declining'
  | 'insufficient_data'

export interface ProjectTrend {
  project_id: number
  project_name: string
  momentum: MomentumLevel
  velocity_score: number
  star_growth_30d: number | null
  contributor_growth_30d: number | null
  active_contributors_30d: number | null
  pr_merged_30d: number | null
  snapshot_count: number
  latest_snapshot_at: string | null
}

// ─── 关键人物识别 ─────────────────────────────────────────────────────────────

export type InfluenceType =
  | 'maintainer'
  | 'bridge'
  | 'rising_star'
  | 'reviewer'
  | 'contributor'

export interface KeyPerson {
  github_handle: string
  display_name: string | null
  avatar_url: string | null
  influence_types: InfluenceType[]
  influence_score: number
  cross_project_count: number
  commit_count_90d: number | null
  pr_count_90d: number | null
  review_count_90d: number | null
  company: string | null
  person_profile_id: number | null
  project_ids: number[]
}

// ─── 企业图谱 ─────────────────────────────────────────────────────────────────

export interface ProjectPresence {
  project_id: number
  project_name: string
  contributor_count: number
  has_maintainer: boolean
  commit_share: number
}

export interface CorporateLandscape {
  company: string
  project_count: number
  strategic_score: number
  has_maintainer: boolean
  total_contributors: number
  projects: ProjectPresence[]
}

// ─── API 调用 ─────────────────────────────────────────────────────────────────

export const getTrends = (momentum?: MomentumLevel) =>
  apiClient.get<ProjectTrend[]>('/insights/trends', { params: momentum ? { momentum } : undefined }).then(r => r.data)

/** 返回全局关键人物列表（跨项目聚合），可按 type 或 limit 筛选 */
export const getPeople = (params?: { type?: InfluenceType; limit?: number }) =>
  apiClient.get<KeyPerson[]>('/insights/people', { params }).then(r => r.data)

export const getCorporate = (params?: { min_projects?: number; limit?: number }) =>
  apiClient.get<CorporateLandscape[]>('/insights/corporate', { params }).then(r => r.data)
