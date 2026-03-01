import apiClient from './index'

export interface EcosystemProject {
  id: number
  name: string
  platform: string
  org_name: string
  repo_name: string | null
  description: string | null
  tags: string[] | null
  is_active: boolean
  last_synced_at: string | null
  added_by_id: number | null
  created_at: string
  auto_sync_enabled: boolean
  sync_interval_hours: number | null
}

export interface EcosystemContributor {
  id: number
  project_id: number
  github_handle: string
  display_name: string | null
  avatar_url: string | null
  role: string | null
  commit_count_90d: number | null
  pr_count_90d: number | null
  star_count: number | null
  followers: number | null
  person_id: number | null
  last_synced_at: string
}

export interface PaginatedContributors {
  items: EcosystemContributor[]
  total: number
  page: number
  page_size: number
}

export interface SyncResult {
  created: number
  updated: number
  errors: number
}

export interface ProjectCreateData {
  name: string
  platform: string
  org_name: string
  repo_name?: string
  community_id?: number | null
  description?: string
  tags?: string[]
  auto_sync_enabled?: boolean
  sync_interval_hours?: number | null
}

export interface ProjectUpdateData {
  name?: string
  description?: string
  tags?: string[]
  is_active?: boolean
  auto_sync_enabled?: boolean
  sync_interval_hours?: number | null
}

export const listProjects = () =>
  apiClient.get<EcosystemProject[]>('/ecosystem').then(r => r.data)

export const createProject = (data: ProjectCreateData) =>
  apiClient.post<EcosystemProject>('/ecosystem', data).then(r => r.data)

export const getProject = (pid: number) =>
  apiClient.get<EcosystemProject>(`/ecosystem/${pid}`).then(r => r.data)

export const updateProject = (pid: number, data: ProjectUpdateData) =>
  apiClient.patch<EcosystemProject>(`/ecosystem/${pid}`, data).then(r => r.data)

export const syncProject = (pid: number) =>
  apiClient.post<SyncResult>(`/ecosystem/${pid}/sync`).then(r => r.data)

export const listContributors = (pid: number, params?: {
  q?: string
  unlinked?: boolean
  page?: number
  page_size?: number
}) =>
  apiClient.get<PaginatedContributors>(`/ecosystem/${pid}/contributors`, { params }).then(r => r.data)

export const importContributorToPeople = (pid: number, handle: string) =>
  apiClient.post<{ action: string; person_id: number }>(`/ecosystem/${pid}/contributors/${handle}/import-person`).then(r => r.data)

export const deleteProject = (pid: number) =>
  apiClient.delete(`/ecosystem/${pid}`)
