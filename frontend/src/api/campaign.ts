import apiClient from './index'

// ─── Types ────────────────────────────────────────────────────────────────────

/** 活动类型：default=默认活动，community_care=社区成员关怀，developer_care=开发者关怀；旧版保留兼容 */
export type CampaignType =
  | 'default'
  | 'community_care'
  | 'developer_care'
  | 'promotion'
  | 'care'
  | 'invitation'
  | 'survey'

export interface CampaignListItem {
  id: number
  community_id: number | null
  name: string
  type: CampaignType
  status: string
  start_date: string | null
  end_date: string | null
  created_at: string
}

export interface CampaignDetail extends CampaignListItem {
  description: string | null
  owner_ids: number[]
  updated_at: string
}

export interface CampaignCreate {
  name: string
  type: CampaignType
  community_id?: number | null
  description?: string | null
  owner_ids?: number[]
  start_date?: string | null
  end_date?: string | null
}

export interface CampaignUpdate extends Partial<CampaignCreate> {
  status?: string
}

export interface PersonSnapshot {
  id: number
  display_name: string
  company: string | null
  email: string | null
  github_handle: string | null
}

export interface ContactOut {
  id: number
  campaign_id: number
  person_id: number
  status: string
  channel: string | null
  added_by: string
  last_contacted_at: string | null
  notes: string | null
  assigned_to_id: number | null
  person: PersonSnapshot | null
}

export interface PaginatedContacts {
  items: ContactOut[]
  total: number
  page: number
  page_size: number
}

export interface ActivityOut {
  id: number
  campaign_id: number
  person_id: number
  action: string
  content: string | null
  outcome: string | null
  operator_id: number | null
  created_at: string
}

export interface CampaignFunnel {
  pending: number
  contacted: number
  blocked: number
  total: number
}

export interface BulkStatusUpdate {
  contact_ids: number[]
  status: string
  notes?: string | null
}

export interface CommitteeSimple {
  id: number
  name: string
  member_count: number
}

export interface CsvImportResult {
  created: number
  matched: number
  skipped: number
  errors: string[]
}

// ─── Campaign CRUD ────────────────────────────────────────────────────────────

export async function listCampaigns(params?: { type?: string; status?: string }) {
  const res = await apiClient.get<CampaignListItem[]>('/campaigns', { params })
  return res.data
}

export async function createCampaign(data: CampaignCreate) {
  const res = await apiClient.post<CampaignDetail>('/campaigns', data)
  return res.data
}

export async function getCampaign(id: number) {
  const res = await apiClient.get<CampaignDetail>(`/campaigns/${id}`)
  return res.data
}

export async function updateCampaign(id: number, data: CampaignUpdate) {
  const res = await apiClient.patch<CampaignDetail>(`/campaigns/${id}`, data)
  return res.data
}

export async function deleteCampaign(id: number) {
  await apiClient.delete(`/campaigns/${id}`)
}

export async function getCampaignFunnel(id: number) {
  const res = await apiClient.get<CampaignFunnel>(`/campaigns/${id}/funnel`)
  return res.data
}

// ─── Contacts ─────────────────────────────────────────────────────────────────

export async function listContacts(
  campaignId: number,
  params?: { status?: string; page?: number; page_size?: number },
) {
  const res = await apiClient.get<PaginatedContacts>(
    `/campaigns/${campaignId}/contacts`,
    { params },
  )
  return res.data
}

export async function addContact(
  campaignId: number,
  data: { person_id: number; channel?: string; notes?: string },
) {
  const res = await apiClient.post<ContactOut>(`/campaigns/${campaignId}/contacts`, data)
  return res.data
}

export async function updateContactStatus(
  campaignId: number,
  contactId: number,
  data: { status: string; channel?: string; notes?: string },
) {
  const res = await apiClient.patch<ContactOut>(
    `/campaigns/${campaignId}/contacts/${contactId}/status`,
    data,
  )
  return res.data
}

export async function bulkUpdateContactStatus(
  campaignId: number,
  data: BulkStatusUpdate,
) {
  const res = await apiClient.patch<{ updated: number }>(
    `/campaigns/${campaignId}/contacts/bulk-status`,
    data,
  )
  return res.data
}

export async function deleteContact(campaignId: number, contactId: number) {
  await apiClient.delete(`/campaigns/${campaignId}/contacts/${contactId}`)
}

export async function importFromEvent(
  campaignId: number,
  data: { event_id: number; channel?: string },
) {
  const res = await apiClient.post<{ created: number; skipped: number }>(
    `/campaigns/${campaignId}/contacts/import-event`,
    data,
  )
  return res.data
}

export async function importFromPeople(
  campaignId: number,
  data: { person_ids: number[]; channel?: string },
) {
  const res = await apiClient.post<{ created: number; skipped: number }>(
    `/campaigns/${campaignId}/contacts/import-people`,
    data,
  )
  return res.data
}

// ─── Committee Import（社区成员关怀专用）──────────────────────────────────────

export async function listAvailableCommittees(campaignId: number) {
  const res = await apiClient.get<CommitteeSimple[]>(
    `/campaigns/${campaignId}/available-committees`,
  )
  return res.data
}

export async function importFromCommittees(
  campaignId: number,
  data: { committee_ids: number[]; channel?: string; assigned_to_id?: number | null },
) {
  const res = await apiClient.post<{ created: number; skipped: number }>(
    `/campaigns/${campaignId}/contacts/import-committee`,
    data,
  )
  return res.data
}

// ─── CSV Import（developer_care / community_care 共用）───────────────────────

export async function importFromCsv(campaignId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await apiClient.post<CsvImportResult>(
    `/campaigns/${campaignId}/contacts/import-csv`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return res.data
}

// ─── Activities ───────────────────────────────────────────────────────────────

export async function listActivities(campaignId: number, contactId: number) {
  const res = await apiClient.get<ActivityOut[]>(
    `/campaigns/${campaignId}/contacts/${contactId}/activities`,
  )
  return res.data
}

export async function addActivity(
  campaignId: number,
  contactId: number,
  data: { action: string; content?: string; outcome?: string },
) {
  const res = await apiClient.post<ActivityOut>(
    `/campaigns/${campaignId}/contacts/${contactId}/activities`,
    data,
  )
  return res.data
}

// ─── Campaign Task ─────────────────────────────────────────────────────────────

export type TaskStatus = 'not_started' | 'in_progress' | 'completed' | 'blocked'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface CampaignTaskOut {
  id: number
  campaign_id: number
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  assignee_ids: number[]
  deadline: string | null
  created_by_id: number | null
  created_at: string
  updated_at: string
}

export interface CampaignTaskCreate {
  title: string
  description?: string | null
  status?: TaskStatus
  priority?: TaskPriority
  assignee_ids?: number[]
  deadline?: string | null
}

export interface CampaignTaskUpdate {
  title?: string
  description?: string | null
  status?: TaskStatus
  priority?: TaskPriority
  assignee_ids?: number[]
  deadline?: string | null
}

export async function listCampaignTasks(campaignId: number) {
  const res = await apiClient.get<CampaignTaskOut[]>(`/campaigns/${campaignId}/tasks`)
  return res.data
}

export async function createCampaignTask(campaignId: number, data: CampaignTaskCreate) {
  const res = await apiClient.post<CampaignTaskOut>(`/campaigns/${campaignId}/tasks`, data)
  return res.data
}

export async function updateCampaignTask(
  campaignId: number,
  taskId: number,
  data: CampaignTaskUpdate,
) {
  const res = await apiClient.patch<CampaignTaskOut>(
    `/campaigns/${campaignId}/tasks/${taskId}`,
    data,
  )
  return res.data
}

export async function deleteCampaignTask(campaignId: number, taskId: number) {
  await apiClient.delete(`/campaigns/${campaignId}/tasks/${taskId}`)
}
