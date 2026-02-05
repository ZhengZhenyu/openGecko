import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

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
  created_at: string
  updated_at: string
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
