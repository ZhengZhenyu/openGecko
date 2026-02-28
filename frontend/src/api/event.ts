import apiClient from './index'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface EventListItem {
  id: number
  community_id: number | null
  community_ids: number[]
  communities: { id: number; name: string }[]
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
  community_ids: number[]
  communities: { id: number; name: string }[]
  title: string
  event_type: string
  template_id: number | null
  status: string
  planned_at: string | null
  duration_hours: number | null
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
  community_ids?: number[]
  template_id?: number | null
  planned_at?: string | null
  duration_hours?: number | null
  location?: string | null
  online_url?: string | null
  description?: string | null
  status?: string
}

export interface EventUpdate extends Partial<Omit<EventCreate, 'status'>> {
  community_ids?: number[]
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
  description: string | null
  is_mandatory: boolean
  responsible_role: string | null
  reference_url: string | null
  status: string
  assignee_ids: number[]
  due_date: string | null
  notes: string | null
  completed_at: string | null
  order: number
}

export interface ChecklistTemplateItem {
  id: number
  phase: string
  title: string
  description: string | null
  is_mandatory: boolean
  responsible_role: string | null
  deadline_offset_days: number | null
  estimated_hours: number | null
  reference_url: string | null
  order: number
}

export interface EventTemplateListItem {
  id: number
  name: string
  event_type: string
  is_public: boolean
  created_at: string
}

export interface EventTemplate {
  id: number
  community_id: number | null
  name: string
  event_type: string
  description: string | null
  is_public: boolean
  created_by_id: number | null
  created_at: string
  checklist_items: ChecklistTemplateItem[]
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
  assignee_ids: number[]
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
  assignee_ids?: number[]
  parent_task_id?: number | null
  order?: number
}

export interface EventTaskUpdate extends Partial<EventTaskCreate> {
  depends_on?: number[]
}

// ─── Event CRUD ───────────────────────────────────────────────────────────────

export async function listEvents(params?: { status?: string; event_type?: string; community_id?: number; keyword?: string; page?: number; page_size?: number }) {
  const res = await apiClient.get<PaginatedEvents>('/events', { params })
  return res.data
}

export async function createEvent(data: EventCreate) {
  const res = await apiClient.post<EventDetail>('/events', data)
  return res.data
}

export async function getEvent(id: number) {
  const res = await apiClient.get<EventDetail>(`/events/${id}`)
  return res.data
}

export async function updateEvent(id: number, data: EventUpdate) {
  const res = await apiClient.patch<EventDetail>(`/events/${id}`, data)
  return res.data
}

export async function updateEventStatus(id: number, status: string) {
  const res = await apiClient.patch<EventDetail>(`/events/${id}/status`, { status })
  return res.data
}

// ─── Checklist ────────────────────────────────────────────────────────────────

export async function getChecklist(eventId: number) {
  const res = await apiClient.get<ChecklistItem[]>(`/events/${eventId}/checklist`)
  return res.data
}

export async function updateChecklistItem(eventId: number, itemId: number, data: Partial<{
  phase: string
  title: string
  description: string | null
  is_mandatory: boolean
  responsible_role: string | null
  reference_url: string | null
  status: string
  assignee_ids: number[]
  due_date: string | null
  notes: string | null
  order: number
}>) {
  const res = await apiClient.patch<ChecklistItem>(`/events/${eventId}/checklist/${itemId}`, data)
  return res.data
}

export async function createChecklistItem(eventId: number, data: {
  phase: string
  title: string
  description?: string | null
  is_mandatory?: boolean
  responsible_role?: string | null
  reference_url?: string | null
  assignee_ids?: number[]
  due_date?: string | null
  notes?: string | null
  order?: number
}) {
  const res = await apiClient.post<ChecklistItem>(`/events/${eventId}/checklist`, data)
  return res.data
}

export async function deleteChecklistItem(eventId: number, itemId: number) {
  await apiClient.delete(`/events/${eventId}/checklist/${itemId}`)
}

// ─── Personnel ────────────────────────────────────────────────────────────────

export async function listPersonnel(eventId: number) {
  const res = await apiClient.get<Personnel[]>(`/events/${eventId}/personnel`)
  return res.data
}

export async function addPersonnel(eventId: number, data: PersonnelCreate) {
  const res = await apiClient.post<Personnel>(`/events/${eventId}/personnel`, data)
  return res.data
}

export async function confirmPersonnel(eventId: number, pid: number, confirmed: string) {
  const res = await apiClient.patch<Personnel>(`/events/${eventId}/personnel/${pid}/confirm`, { confirmed })
  return res.data
}

// ─── Feedback ─────────────────────────────────────────────────────────────────

export async function listFeedback(eventId: number) {
  const res = await apiClient.get<FeedbackItem[]>(`/events/${eventId}/feedback`)
  return res.data
}

export async function createFeedback(eventId: number, data: { content: string; category?: string; raised_by?: string }) {
  const res = await apiClient.post<FeedbackItem>(`/events/${eventId}/feedback`, data)
  return res.data
}

export async function updateFeedback(eventId: number, fid: number, data: { status?: string; assignee_id?: number | null }) {
  const res = await apiClient.patch<FeedbackItem>(`/events/${eventId}/feedback/${fid}`, data)
  return res.data
}

export async function linkIssue(eventId: number, fid: number, data: {
  platform: string
  repo: string
  issue_number: number
  issue_url?: string
  issue_type?: string
}) {
  const res = await apiClient.post<IssueLink>(`/events/${eventId}/feedback/${fid}/links`, data)
  return res.data
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export async function listTasks(eventId: number) {
  const res = await apiClient.get<EventTask[]>(`/events/${eventId}/tasks`)
  return res.data
}

export async function createTask(eventId: number, data: EventTaskCreate) {
  const res = await apiClient.post<EventTask>(`/events/${eventId}/tasks`, data)
  return res.data
}

export async function updateTask(eventId: number, tid: number, data: EventTaskUpdate) {
  const res = await apiClient.patch<EventTask>(`/events/${eventId}/tasks/${tid}`, data)
  return res.data
}

export async function deleteTask(eventId: number, tid: number) {
  await apiClient.delete(`/events/${eventId}/tasks/${tid}`)
}

export async function deleteEvent(id: number): Promise<void> {
  await apiClient.delete(`/events/${id}`)
}

// ─── Event Templates ──────────────────────────────────────────────────────────

export async function listTemplates() {
  const res = await apiClient.get<EventTemplateListItem[]>('/event-templates')
  return res.data
}

export async function getTemplate(id: number) {
  const res = await apiClient.get<EventTemplate>(`/event-templates/${id}`)
  return res.data
}

export async function createTemplate(data: {
  name: string
  event_type: string
  description?: string | null
  is_public?: boolean
}) {
  const res = await apiClient.post<EventTemplate>('/event-templates', data)
  return res.data
}

export async function updateTemplate(id: number, data: {
  name?: string
  event_type?: string
  description?: string | null
  is_public?: boolean
}) {
  const res = await apiClient.patch<EventTemplate>(`/event-templates/${id}`, data)
  return res.data
}

export async function addTemplateItem(templateId: number, data: {
  phase: string
  title: string
  description?: string | null
  is_mandatory?: boolean
  responsible_role?: string | null
  deadline_offset_days?: number | null
  estimated_hours?: number | null
  reference_url?: string | null
  order?: number
}) {
  const res = await apiClient.post<ChecklistTemplateItem>(`/event-templates/${templateId}/items`, data)
  return res.data
}

export async function updateTemplateItem(templateId: number, itemId: number, data: Partial<{
  phase: string
  title: string
  description: string | null
  is_mandatory: boolean
  responsible_role: string | null
  deadline_offset_days: number | null
  estimated_hours: number | null
  reference_url: string | null
  order: number
}>) {
  const res = await apiClient.patch<ChecklistTemplateItem>(`/event-templates/${templateId}/items/${itemId}`, data)
  return res.data
}

export async function deleteTemplateItem(templateId: number, itemId: number) {
  await apiClient.delete(`/event-templates/${templateId}/items/${itemId}`)
}

export async function deleteTemplate(templateId: number) {
  await apiClient.delete(`/event-templates/${templateId}`)
}
