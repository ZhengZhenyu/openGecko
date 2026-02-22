import apiClient from './index'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CampaignListItem {
  id: number
  community_id: number
  name: string
  type: string
  status: string
  target_count: number | null
  start_date: string | null
  end_date: string | null
  created_at: string
}

export interface CampaignDetail extends CampaignListItem {
  description: string | null
  owner_id: number | null
  updated_at: string
}

export interface CampaignCreate {
  name: string
  type: string
  description?: string | null
  target_count?: number | null
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
  responded: number
  converted: number
  declined: number
  total: number
}

// ─── Campaign CRUD ────────────────────────────────────────────────────────────

export async function listCampaigns(params?: { type?: string; status?: string }) {
  const res = await apiClient.get<CampaignListItem[]>('/api/campaigns', { params })
  return res.data
}

export async function createCampaign(data: CampaignCreate) {
  const res = await apiClient.post<CampaignDetail>('/api/campaigns', data)
  return res.data
}

export async function getCampaign(id: number) {
  const res = await apiClient.get<CampaignDetail>(`/api/campaigns/${id}`)
  return res.data
}

export async function updateCampaign(id: number, data: CampaignUpdate) {
  const res = await apiClient.patch<CampaignDetail>(`/api/campaigns/${id}`, data)
  return res.data
}

export async function getCampaignFunnel(id: number) {
  const res = await apiClient.get<CampaignFunnel>(`/api/campaigns/${id}/funnel`)
  return res.data
}

// ─── Contacts ─────────────────────────────────────────────────────────────────

export async function listContacts(campaignId: number, params?: { status?: string; page?: number; page_size?: number }) {
  const res = await apiClient.get<PaginatedContacts>(`/api/campaigns/${campaignId}/contacts`, { params })
  return res.data
}

export async function addContact(campaignId: number, data: { person_id: number; channel?: string; notes?: string }) {
  const res = await apiClient.post<ContactOut>(`/api/campaigns/${campaignId}/contacts`, data)
  return res.data
}

export async function updateContactStatus(campaignId: number, contactId: number, data: { status: string; channel?: string; notes?: string }) {
  const res = await apiClient.patch<ContactOut>(`/api/campaigns/${campaignId}/contacts/${contactId}/status`, data)
  return res.data
}

export async function importFromEvent(campaignId: number, data: { event_id: number; channel?: string }) {
  const res = await apiClient.post<{ created: number; skipped: number }>(`/api/campaigns/${campaignId}/contacts/import-event`, data)
  return res.data
}

export async function importFromPeople(campaignId: number, data: { person_ids: number[]; channel?: string }) {
  const res = await apiClient.post<{ created: number; skipped: number }>(`/api/campaigns/${campaignId}/contacts/import-people`, data)
  return res.data
}

// ─── Activities ───────────────────────────────────────────────────────────────

export async function listActivities(campaignId: number, contactId: number) {
  const res = await apiClient.get<ActivityOut[]>(`/api/campaigns/${campaignId}/contacts/${contactId}/activities`)
  return res.data
}

export async function addActivity(campaignId: number, contactId: number, data: { action: string; content?: string; outcome?: string }) {
  const res = await apiClient.post<ActivityOut>(`/api/campaigns/${campaignId}/contacts/${contactId}/activities`, data)
  return res.data
}
