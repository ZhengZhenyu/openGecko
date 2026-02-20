import apiClient from './index'

// ===== Response Types (mirrors backend schemas/community_dashboard.py) =====

export interface CommunityMetrics {
  total_contents: number
  published_contents: number
  reviewing_contents: number
  draft_contents: number
  total_committees: number
  total_members: number
  upcoming_meetings: number
  active_channels: number
}

export interface MonthlyTrend {
  month: string  // "2025-08"
  count: number
}

export interface ChannelStats {
  wechat: number
  hugo: number
  csdn: number
  zhihu: number
}

export interface RecentContentItem {
  id: number
  title: string
  status: string
  work_status: string | null
  created_at: string
  owner_name: string
}

export interface UpcomingMeetingItem {
  id: number
  title: string
  scheduled_at: string
  committee_name: string
  status: string
}

export interface CalendarEvent {
  id: string
  type: string  // "meeting" | "publish" | "member_join"
  title: string
  date: string
  color: string
  resource_id: number
  resource_type: string
}

export interface CommunityDashboardResponse {
  metrics: CommunityMetrics
  monthly_trend: MonthlyTrend[]
  channel_stats: ChannelStats
  recent_contents: RecentContentItem[]
  upcoming_meetings: UpcomingMeetingItem[]
  calendar_events: CalendarEvent[]
}

// ===== Superuser Overview =====

export interface CommunityOverviewItem {
  id: number
  name: string
  slug: string
  is_active: boolean
  member_count: number
  total_contents: number
  published_contents: number
  reviewing_contents: number
  committee_count: number
  upcoming_meeting_count: number
  active_channel_count: number
}

export interface SuperuserOverviewResponse {
  total_communities: number
  communities: CommunityOverviewItem[]
}

// ===== API Functions =====

/** 获取社区工作台聚合数据 */
export async function getCommunityDashboard(
  communityId: number
): Promise<CommunityDashboardResponse> {
  const { data } = await apiClient.get<CommunityDashboardResponse>(
    `/communities/${communityId}/dashboard`,
    { headers: { 'X-Community-Id': String(communityId) } }
  )
  return data
}

/** 超管全局社区总览（批量统计，消除 N+1） */
export async function getSuperuserOverview(): Promise<SuperuserOverviewResponse> {
  const { data } = await apiClient.get<SuperuserOverviewResponse>(
    '/communities/overview/stats'
  )
  return data
}
