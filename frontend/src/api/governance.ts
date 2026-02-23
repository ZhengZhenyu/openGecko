import apiClient from './index'

// ==================== Types ====================

export interface Committee {
  id: number
  community_id: number
  name: string
  slug: string
  description?: string
  is_active: boolean
  meeting_frequency?: string
  notification_email?: string
  notification_wechat?: string
  established_at?: string
  member_count: number
  created_at: string
  updated_at: string
}

export interface CommitteeMember {
  id: number
  committee_id: number
  name: string
  email: string
  phone?: string
  wechat?: string
  organization: string
  gitcode_id?: string
  github_id?: string
  roles: string[]
  term_start?: string
  term_end?: string
  is_active: boolean
  bio?: string
  avatar_url?: string
  joined_at: string
  created_at: string
}

export interface CommitteeWithMembers extends Committee {
  members: CommitteeMember[]
}

export interface CommitteeCreate {
  name: string
  slug: string
  description?: string
  notification_email?: string
  notification_wechat?: string
}

export interface CommitteeUpdate {
  name?: string
  description?: string
  is_active?: boolean
  notification_email?: string
  notification_wechat?: string
}

export interface CommitteeMemberCreate {
  name: string
  email: string
  phone?: string
  wechat?: string
  organization: string
  gitcode_id?: string
  github_id?: string
  roles?: string[]
  term_start?: string
  term_end?: string
  bio?: string
}

export interface CommitteeMemberUpdate {
  name?: string
  email?: string
  phone?: string
  wechat?: string
  organization?: string
  gitcode_id?: string
  github_id?: string
  roles?: string[]
  term_start?: string
  term_end?: string
  is_active?: boolean
  bio?: string
  avatar_url?: string
}

export interface Meeting {
  id: number
  committee_id: number
  community_id: number
  title: string
  description?: string
  scheduled_at: string
  duration: number
  location_type?: string
  location?: string       // 线下会议地址（offline / hybrid）
  online_url?: string     // 线上会议链接（online / hybrid）
  status: string
  reminder_sent: boolean
  created_by_user_id?: number
  created_at: string
  updated_at: string
}

export interface MeetingDetail extends Meeting {
  agenda?: string
  minutes?: string
  attachments?: any[]
  committee_name?: string
}

export interface MeetingCreate {
  committee_id: number
  title: string
  description?: string
  scheduled_at: string
  duration?: number
  location_type?: string
  location?: string       // 线下会议地址（offline / hybrid）
  online_url?: string     // 线上会议链接（online / hybrid）
  agenda?: string
  reminder_before_hours?: number
  assignee_ids?: number[]
}

export interface MeetingUpdate {
  title?: string
  description?: string
  scheduled_at?: string
  duration?: number
  location_type?: string
  location?: string       // 线下会议地址（offline / hybrid）
  online_url?: string     // 线上会议链接（online / hybrid）
  status?: string
  agenda?: string
  reminder_before_hours?: number
  assignee_ids?: number[]
}

export interface MeetingReminder {
  id: number
  meeting_id: number
  reminder_type: string
  scheduled_at: string
  sent_at?: string
  notification_channels: string[]
  status: string
  error_message?: string
  created_at: string
}

// ==================== Committee APIs ====================

export async function listCommittees(params?: { is_active?: boolean }) {
  const { data } = await apiClient.get<Committee[]>('/committees', { params })
  return data
}

export async function createCommittee(data: CommitteeCreate) {
  const response = await apiClient.post<Committee>('/committees', data)
  return response.data
}

export async function getCommittee(id: number) {
  const { data } = await apiClient.get<CommitteeWithMembers>(`/committees/${id}`)
  return data
}

export async function updateCommittee(id: number, data: CommitteeUpdate) {
  const response = await apiClient.put<Committee>(`/committees/${id}`, data)
  return response.data
}

export async function deleteCommittee(id: number) {
  await apiClient.delete(`/committees/${id}`)
}

// ==================== Committee Member APIs ====================

export async function listCommitteeMembers(committeeId: number, params?: { is_active?: boolean }) {
  const { data } = await apiClient.get<CommitteeMember[]>(`/committees/${committeeId}/members`, { params })
  return data
}

export async function createCommitteeMember(committeeId: number, data: CommitteeMemberCreate) {
  const response = await apiClient.post<CommitteeMember>(`/committees/${committeeId}/members`, data)
  return response.data
}

export async function updateCommitteeMember(
  committeeId: number,
  memberId: number,
  data: CommitteeMemberUpdate
) {
  const response = await apiClient.put<CommitteeMember>(`/committees/${committeeId}/members/${memberId}`, data)
  return response.data
}

export async function deleteCommitteeMember(committeeId: number, memberId: number) {
  await apiClient.delete(`/committees/${committeeId}/members/${memberId}`)
}

// ==================== Meeting APIs ====================

export async function listMeetings(params?: {
  committee_id?: number
  start_date?: string
  end_date?: string
  skip?: number
  limit?: number
}) {
  const { data } = await apiClient.get<Meeting[]>('/meetings', { params })
  return data
}

export async function createMeeting(data: MeetingCreate) {
  const response = await apiClient.post<Meeting>('/meetings', data)
  return response.data
}

export async function getMeeting(id: number) {
  const { data } = await apiClient.get<MeetingDetail>(`/meetings/${id}`)
  return data
}

export async function updateMeeting(id: number, data: MeetingUpdate) {
  const response = await apiClient.put<Meeting>(`/meetings/${id}`, data)
  return response.data
}

export async function deleteMeeting(id: number) {
  await apiClient.delete(`/meetings/${id}`)
}

export async function updateMeetingMinutes(id: number, minutes: string) {
  const { data } = await apiClient.put<MeetingDetail>(`/meetings/${id}/minutes`, { minutes })
  return data
}

export async function getMeetingMinutes(id: number) {
  const { data } = await apiClient.get<{ minutes: string }>(`/meetings/${id}/minutes`)
  return data
}

export async function listMeetingReminders(meetingId: number) {
  const { data } = await apiClient.get<MeetingReminder[]>(`/meetings/${meetingId}/reminders`)
  return data
}

export async function createMeetingReminder(meetingId: number, reminderType: string) {
  const { data } = await apiClient.post<MeetingReminder>(`/meetings/${meetingId}/reminders`, { reminder_type: reminderType })
  return data
}

// ==================== Meeting Participant APIs ====================

export interface MeetingParticipant {
  id: number
  meeting_id: number
  name: string
  email: string
  source: string
  created_at: string
}

export interface MeetingParticipantCreate {
  name: string
  email: string
}

export interface MeetingParticipantImportResult {
  total_imported: number
  skipped_count: number
  added_count: number
}

export async function listMeetingParticipants(meetingId: number) {
  const { data } = await apiClient.get<MeetingParticipant[]>(`/meetings/${meetingId}/participants`)
  return data
}

export async function addMeetingParticipant(meetingId: number, participant: MeetingParticipantCreate) {
  const { data } = await apiClient.post<MeetingParticipant>(`/meetings/${meetingId}/participants`, participant)
  return data
}

export async function deleteMeetingParticipant(meetingId: number, participantId: number) {
  await apiClient.delete(`/meetings/${meetingId}/participants/${participantId}`)
}

export async function importParticipantsFromCommittee(meetingId: number) {
  const { data } = await apiClient.post<MeetingParticipantImportResult>(`/meetings/${meetingId}/participants/import`)
  return data
}
