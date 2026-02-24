import apiClient from './index'

const api = apiClient

export interface Content {
  id: number
  title: string
  content_markdown: string
  content_html: string
  source_type: string
  source_file: string | null
  author: string
  tags: string[]
  category: string
  cover_image: string | null
  status: string
  work_status: string
  owner_id: number | null
  community_id: number
  created_by_user_id: number | null
  assignee_ids: number[]
  community_ids: number[]
  scheduled_publish_at: string | null
  created_at: string
  updated_at: string
}

export interface ContentListItem {
  id: number
  title: string
  source_type: string
  author: string
  tags: string[]
  category: string
  status: string
  work_status: string
  community_id: number | null
  owner_id: number | null
  scheduled_publish_at: string | null
  created_at: string
  updated_at: string
  assignee_names: string[]
}

export interface ContentCalendarItem {
  id: number
  title: string
  status: string
  source_type: string
  author: string
  category: string
  scheduled_publish_at: string | null
  created_at: string
}

export interface PaginatedContents {
  items: ContentListItem[]
  total: number
  page: number
  page_size: number
}

export async function fetchContents(params: {
  page?: number
  page_size?: number
  status?: string
  source_type?: string
  keyword?: string
  community_id?: number
  unscheduled?: boolean
}): Promise<PaginatedContents> {
  const { data } = await api.get('/contents', { params })
  return data
}

export async function fetchContent(id: number): Promise<Content> {
  const { data } = await api.get(`/contents/${id}`)
  return data
}

export async function createContent(payload: Partial<Content>): Promise<Content> {
  const { data } = await api.post('/contents', payload)
  return data
}

export async function updateContent(id: number, payload: Partial<Content>): Promise<Content> {
  const { data } = await api.put(`/contents/${id}`, payload)
  return data
}

export async function deleteContent(id: number): Promise<void> {
  await api.delete(`/contents/${id}`)
}

export async function updateContentStatus(id: number, status: string): Promise<Content> {
  const { data } = await api.patch(`/contents/${id}/status`, { status })
  return data
}

export async function uploadFile(file: File): Promise<Content> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/contents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function uploadCoverImage(contentId: number, file: File): Promise<Content> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post(`/contents/${contentId}/cover`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// Collaborator management

export interface Collaborator {
  id: number
  username: string
  email: string
}

export async function listCollaborators(contentId: number): Promise<Collaborator[]> {
  const { data } = await api.get(`/contents/${contentId}/collaborators`)
  return data
}

export async function addCollaborator(contentId: number, userId: number): Promise<void> {
  await api.post(`/contents/${contentId}/collaborators/${userId}`)
}

export async function removeCollaborator(contentId: number, userId: number): Promise<void> {
  await api.delete(`/contents/${contentId}/collaborators/${userId}`)
}

export async function transferOwnership(contentId: number, newOwnerId: number): Promise<Content> {
  const { data } = await api.put(`/contents/${contentId}/owner/${newOwnerId}`)
  return data
}

// Calendar API

export async function fetchCalendarEvents(params: {
  start: string
  end: string
  status?: string
}): Promise<ContentCalendarItem[]> {
  const { data } = await api.get('/contents/calendar/events', { params })
  return data
}

export async function updateContentSchedule(
  id: number,
  scheduledPublishAt: string | null
): Promise<Content> {
  const { data } = await api.patch(`/contents/${id}/schedule`, {
    scheduled_publish_at: scheduledPublishAt,
  })
  return data
}
