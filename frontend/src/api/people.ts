import apiClient from './index'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CommunityRoleOut {
  id: number
  community_name: string
  project_url: string | null
  role: string
  role_label: string | null
  is_current: boolean
  started_at: string | null
  ended_at: string | null
  source_url: string | null
}

export interface PersonListOut {
  id: number
  display_name: string
  avatar_url: string | null
  github_handle: string | null
  email: string | null
  company: string | null
  source: string
  created_at: string
}

export interface PersonOut {
  id: number
  display_name: string
  avatar_url: string | null
  github_handle: string | null
  gitcode_handle: string | null
  email: string | null
  phone: string | null
  company: string | null
  location: string | null
  bio: string | null
  tags: string[]
  notes: string | null
  source: string
  created_by_id: number | null
  created_at: string
  updated_at: string
  community_roles: CommunityRoleOut[]
}

export interface PersonCreate {
  display_name: string
  avatar_url?: string | null
  github_handle?: string | null
  gitcode_handle?: string | null
  email?: string | null
  phone?: string | null
  company?: string | null
  location?: string | null
  bio?: string | null
  tags?: string[]
  notes?: string | null
  source?: string
}

export interface PersonUpdate {
  display_name?: string
  avatar_url?: string | null
  github_handle?: string | null
  gitcode_handle?: string | null
  email?: string | null
  phone?: string | null
  company?: string | null
  location?: string | null
  bio?: string | null
  tags?: string[]
  notes?: string | null
}

export interface CommunityRoleCreate {
  community_name: string
  project_url?: string | null
  role: string
  role_label?: string | null
  is_current?: boolean
  started_at?: string | null
  ended_at?: string | null
  source_url?: string | null
}

export interface PaginatedPeople {
  items: PersonListOut[]
  total: number
  page: number
  page_size: number
}

// ─── People CRUD ──────────────────────────────────────────────────────────────

export async function listPeople(params?: {
  q?: string
  tag?: string
  company?: string
  source?: string
  page?: number
  page_size?: number
}) {
  const res = await apiClient.get<PaginatedPeople>('/people', { params })
  return res.data
}

export async function createPerson(data: PersonCreate) {
  const res = await apiClient.post<PersonOut>('/people', data)
  return res.data
}

export async function getPerson(id: number) {
  const res = await apiClient.get<PersonOut>(`/people/${id}`)
  return res.data
}

export async function updatePerson(id: number, data: PersonUpdate) {
  const res = await apiClient.patch<PersonOut>(`/people/${id}`, data)
  return res.data
}

export async function deletePerson(id: number) {
  await apiClient.delete(`/people/${id}`)
}

// ─── Community Roles ─────────────────────────────────────────────────────────

export async function listPersonRoles(personId: number) {
  const res = await apiClient.get<CommunityRoleOut[]>(`/people/${personId}/roles`)
  return res.data
}

export async function addPersonRole(personId: number, data: CommunityRoleCreate) {
  const res = await apiClient.post<CommunityRoleOut>(`/people/${personId}/roles`, data)
  return res.data
}
