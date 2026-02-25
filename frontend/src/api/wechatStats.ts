import apiClient from './index'

const api = apiClient

// ── Types ──

export interface WechatArticleStatOut {
  id: number
  publish_record_id: number
  article_category: string
  stat_date: string
  read_count: number
  read_user_count: number
  read_original_count: number
  like_count: number
  wow_count: number
  share_count: number
  comment_count: number
  favorite_count: number
  forward_count: number
  new_follower_count: number
  unfollow_count: number
  collected_at: string
}

export interface WechatDailyStatCreate {
  publish_record_id: number
  article_category?: string
  stat_date: string
  read_count?: number
  read_user_count?: number
  read_original_count?: number
  like_count?: number
  wow_count?: number
  share_count?: number
  comment_count?: number
  favorite_count?: number
  forward_count?: number
  new_follower_count?: number
  unfollow_count?: number
}

export interface TrendDataPoint {
  date: string
  read_count: number
  read_user_count: number
  like_count: number
  wow_count: number
  share_count: number
  comment_count: number
  favorite_count: number
  forward_count: number
  new_follower_count: number
}

export interface TrendResponse {
  period_type: string
  category: string | null
  data_points: TrendDataPoint[]
}

export interface CategorySummary {
  category: string
  category_label: string
  article_count: number
  total_read_count: number
  total_like_count: number
  total_share_count: number
  total_comment_count: number
  avg_read_count: number
}

export interface WechatStatsOverview {
  total_wechat_articles: number
  total_read_count: number
  total_interaction_count: number
  category_summary: CategorySummary[]
  top_articles: ArticleRankItem[]
}

export interface ArticleRankItem {
  publish_record_id: number
  content_id: number
  title: string
  article_category: string
  read_count: number
  like_count: number
  share_count: number
  comment_count: number
  published_at: string | null
}

// ── Sync Types ──

export interface SyncArticlesResponse {
  synced: number
  skipped: number
  total: number
}

export interface SyncStatsResponse {
  days_processed: number
  stats_written: number
}

// ── API Functions ──

export async function getWechatStatsOverview(): Promise<WechatStatsOverview> {
  const { data } = await api.get('/wechat-stats/overview')
  return data
}

export async function getWechatStatsTrend(params: {
  period_type?: string
  category?: string
  start_date?: string
  end_date?: string
}): Promise<TrendResponse> {
  const { data } = await api.get('/wechat-stats/trend', { params })
  return data
}

export async function getWechatArticleRanking(params: {
  category?: string
  limit?: number
}): Promise<ArticleRankItem[]> {
  const { data } = await api.get('/wechat-stats/ranking', { params })
  return data
}

export async function getArticleDailyStats(
  publishRecordId: number,
  params?: { start_date?: string; end_date?: string }
): Promise<WechatArticleStatOut[]> {
  const { data } = await api.get(`/wechat-stats/articles/${publishRecordId}/daily`, { params })
  return data
}

export async function updateArticleCategory(
  publishRecordId: number,
  article_category: string
): Promise<{ updated: number; article_category: string }> {
  const { data } = await api.put(`/wechat-stats/articles/${publishRecordId}/category`, {
    article_category,
  })
  return data
}

export async function createDailyStat(
  payload: WechatDailyStatCreate
): Promise<WechatArticleStatOut> {
  const { data } = await api.post('/wechat-stats/daily-stats', payload)
  return data
}

export async function batchCreateDailyStats(
  items: WechatDailyStatCreate[]
): Promise<WechatArticleStatOut[]> {
  const { data } = await api.post('/wechat-stats/daily-stats/batch', { items })
  return data
}

export async function rebuildAggregates(params: {
  period_type?: string
  start_date?: string
  end_date?: string
}): Promise<{ rebuilt_count: number; period_type: string }> {
  const { data } = await api.post('/wechat-stats/aggregates/rebuild', null, { params })
  return data
}

// ── Sync Functions ──

export async function syncWechatArticles(): Promise<SyncArticlesResponse> {
  const { data } = await api.post('/wechat-stats/sync/articles')
  return data
}

export async function syncWechatStats(params: {
  start_date: string
  end_date: string
}): Promise<SyncStatsResponse> {
  const { data } = await api.post('/wechat-stats/sync/stats', params)
  return data
}
