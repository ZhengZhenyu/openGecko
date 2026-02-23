import apiClient from './index'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface EventListItem {
  id: number
  title: string
  event_type: string
  status: string
  planned_at: string | null
  location: string | null
  owner_id: number | null
  created_at: string
}

export interface EventDetail {
  id: number
  community_id: number | null
  title: string
  event_type: string
  template_id: number | null
  status: string
  planned_at: string | null
  duration_minutes: number | null
  location: string | null
  online_url: string | null
  description: string | null
  cover_image_url: string | null
  owner_id: number | null
  attendee_count: number | null
  online_count: number | null
  offline_count: number | null
  registration_count: number | null
  result_summary: string | null
  media_urls: string[]
  created_at: string
  updated_at: string
}

export interface EventCreate {
  title: string
  event_type?: string
  community_id?: number | null
  template_id?: number | null
  planned_at?: string | null
  duration_minutes?: number | null
  location?: string | null
  online_url?: string | null
  description?: string | null
}

export interface EventUpdate extends Partial<EventCreate> {
  attendee_count?: number | null
  result_summary?: string | null
}

export interface PaginatedEvents {
  items: EventListItem[]
  total: number
  page: number
  page_size: number
}

export interface ChecklistItem {
  id: number
  phase: string
  title: string
  status: string
  assignee_id: number | null
  due_date: string | null
  notes: string | null
  order: number
}

export interface Personnel {
  id: number
  role: string
  role_label: string | null
  assignee_type: string
  user_id: number | null
  person_id: number | null
  confirmed: string
  time_slot: string | null
  notes: string | null
  order: number
}

export interface PersonnelCreate {
  role: string
  role_label?: string | null
  assignee_type: string
  user_id?: number | null
  person_id?: number | null
  time_slot?: string | null
  notes?: string | null
  order?: number
}

export interface FeedbackItem {
  id: number
  content: string
  category: string
  raised_by: string | null
  raised_by_person_id: number | null
  status: string
  assignee_id: number | null
  created_at: string
  issue_links: IssueLink[]
}

export interface IssueLink {
  id: number
  platform: string
  repo: string
  issue_number: number
  issue_url: string
  issue_type: string
  issue_status: string
  linked_at: string
  linked_by_id: number | null
}

export interface EventTask {
  id: number
  event_id: number
  title: string
  task_type: string
  phase: string
  start_date: string | null
  end_date: string | null
  progress: number
  status: string
  depends_on: number[]
  parent_task_id: number | null
  order: number
  children: EventTask[]
}

export interface EventTaskCreate {
  title: string
  task_type?: string
  phase?: string
  start_date?: string | null
  end_date?: string | null
  progress?: number
  status?: string
  parent_task_id?: number | null
  order?: number
}

export interface EventTaskUpdate extends Partial<EventTaskCreate> {
  depends_on?: number[]
}

// ─── Event CRUD ───────────────────────────────────────────────────────────────

export async function listEvents(params?: { status?: string; event_type?: string; page?: number; page_size?: number }) {
  const res = await apiClient.get<PaginatedEvents>('/api/events', { params })
  return res.data
}

export async function createEvent(data: EventCreate) {
  const res = await apiClient.post<EventDetail>('/api/events', data)
  return res.data
}

export async function getEvent(id: number) {
  const res = await apiClient.get<EventDetail>(`/api/events/${id}`)
  return res.data
}

export async function updateEvent(id: number, data: EventUpdate) {
  const res = await apiClient.patch<EventDetail>(`/api/events/${id}`, data)
  return res.data
}

export async function updateEventStatus(id: number, status: string) {
  const res = await apiClient.patch<EventDetail>(`/api/events/${id}/status`, { status })
  return res.data
}

// ─── Checklist ────────────────────────────────────────────────────────────────

export async function getChecklist(eventId: number) {
  const res = await apiClient.get<ChecklistItem[]>(`/api/events/${eventId}/checklist`)
  return res.data
}

export async function updateChecklistItem(eventId: number, itemId: number, data: { status?: string; notes?: string; due_date?: string | null }) {
  const res = await apiClient.patch<ChecklistItem>(`/api/events/${eventId}/checklist/${itemId}`, data)
  return res.data
}

// ─── Personnel ────────────────────────────────────────────────────────────────

export async function listPersonnel(eventId: number) {
  const res = await apiClient.get<Personnel[]>(`/api/events/${eventId}/personnel`)
  return res.data
}

export async function addPersonnel(eventId: number, data: PersonnelCreate) {
  const res = await apiClient.post<Personnel>(`/api/events/${eventId}/personnel`, data)
  return res.data
}

export async function confirmPersonnel(eventId: number, pid: number, confirmed: string) {
  const res = await apiClient.patch<Personnel>(`/api/events/${eventId}/personnel/${pid}/confirm`, { confirmed })
  return res.data
}

// ─── Feedback ─────────────────────────────────────────────────────────────────

export async function listFeedback(eventId: number) {
  const res = await apiClient.get<FeedbackItem[]>(`/api/events/${eventId}/feedback`)
  return res.data
}

export async function createFeedback(eventId: number, data: { content: string; category?: string; raised_by?: string }) {
  const res = await apiClient.post<FeedbackItem>(`/api/events/${eventId}/feedback`, data)
  return res.data
}

export async function updateFeedback(eventId: number, fid: number, data: { status?: string; assignee_id?: number | null }) {
  const res = await apiClient.patch<FeedbackItem>(`/api/events/${eventId}/feedback/${fid}`, data)
  return res.data
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export async function listTasks(eventId: number) {
  const res = await apiClient.get<EventTask[]>(`/api/events/${eventId}/tasks`)
  return res.data
}

export async function createTask(eventId: number, data: EventTaskCreate) {
  const res = await apiClient.post<EventTask>(`/api/events/${eventId}/tasks`, data)
  return res.data
}

export async function updateTask(eventId: number, tid: number, data: EventTaskUpdate) {
  const res = await apiClient.patch<EventTask>(`/api/events/${eventId}/tasks/${tid}`, data)
  return res.data
}

export async function deleteTask(eventId: number, tid: number) {
  await apiClient.delete(`/api/events/${eventId}/tasks/${tid}`)
}
