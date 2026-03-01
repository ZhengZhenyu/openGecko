import apiClient from './index'

const api = apiClient

export interface PublishRecord {
  id: number
  content_id: number
  channel: string
  status: string
  platform_article_id: string | null
  platform_url: string | null
  published_at: string | null
  error_message: string | null
  created_at: string
}

export interface ChannelPreview {
  channel: string
  title: string
  content: string
  format: string
}

export interface CopyContent {
  channel: string
  title: string
  content: string
  format: string
  platform: string
}

export interface AnalyticsOverview {
  total_contents: number
  total_published: number
  channels: Record<string, number>
}

export interface ChannelConfig {
  id: number
  channel: string
  config: Record<string, string>
  enabled: boolean
}

export async function publishToWechat(contentId: number): Promise<PublishRecord> {
  const { data } = await api.post(`/publish/${contentId}/wechat`)
  return data
}

export async function publishToHugo(contentId: number): Promise<PublishRecord> {
  const { data } = await api.post(`/publish/${contentId}/hugo`)
  return data
}

export async function getPreview(contentId: number, channel: string): Promise<ChannelPreview> {
  const { data } = await api.get(`/publish/${contentId}/preview/${channel}`)
  return data
}

export async function getCopyContent(contentId: number, channel: string): Promise<CopyContent> {
  const { data } = await api.get(`/publish/${contentId}/copy/${channel}`)
  return data
}

export async function getPublishRecords(contentId?: number): Promise<PublishRecord[]> {
  const { data } = await api.get('/publish/records', { params: contentId ? { content_id: contentId } : {} })
  return data
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const { data } = await api.get('/analytics/overview')
  return data
}

export async function getPublishTrend(days = 30): Promise<{ items: { date: string; count: number }[]; days: number }> {
  const { data } = await api.get('/analytics/trend/daily', { params: { days } })
  return data
}

export async function getChannelConfigs(): Promise<ChannelConfig[]> {
  const { data } = await api.get('/analytics/settings/channels')
  return data
}

export async function updateChannelConfig(
  channel: string,
  payload: { config?: Record<string, string>; enabled?: boolean }
): Promise<ChannelConfig> {
  const { data } = await api.put(`/analytics/settings/channels/${channel}`, payload)
  return data
}
