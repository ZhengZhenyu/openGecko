import apiClient from './index'

const api = apiClient

export interface AuditLogItem {
  id: number
  username: string
  full_name: string
  action: string
  resource_type: string
  resource_id: number | null
  community_id: number | null
  details: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}

export interface AuditLogsResponse {
  items: AuditLogItem[]
  total: number
  page: number
  page_size: number
}

export interface AuditLogFilters {
  action?: string
  resource_type?: string
  community_id?: number
  username?: string
  from_date?: string
  to_date?: string
  page?: number
  page_size?: number
}

export async function getAuditLogs(filters: AuditLogFilters = {}): Promise<AuditLogsResponse> {
  const params: Record<string, string | number> = {}
  if (filters.action)        params.action = filters.action
  if (filters.resource_type) params.resource_type = filters.resource_type
  if (filters.community_id)  params.community_id = filters.community_id
  if (filters.username)      params.username = filters.username
  if (filters.from_date)     params.from_date = filters.from_date
  if (filters.to_date)       params.to_date = filters.to_date
  params.page      = filters.page      ?? 1
  params.page_size = filters.page_size ?? 20
  const { data } = await api.get('/admin/audit-logs', { params })
  return data
}
