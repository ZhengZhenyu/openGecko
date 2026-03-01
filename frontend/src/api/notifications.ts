import apiClient from './index'

// ─── 类型定义 ────────────────────────────────────────────────────────────────

export interface Notification {
  id: number
  type: string
  title: string
  body: string | null
  is_read: boolean
  read_at: string | null
  created_at: string
  resource_type: string | null
  resource_id: number | null
}

export interface NotificationList {
  items: Notification[]
  total: number
  unread_count: number
}

// ─── API 函数 ─────────────────────────────────────────────────────────────────

export const getNotifications = (params?: { unread_only?: boolean; skip?: number; limit?: number }) =>
  apiClient.get<NotificationList>('/notifications', { params }).then(r => r.data)

export const getUnreadCount = () =>
  apiClient.get<{ count: number }>('/notifications/unread-count').then(r => r.data)

export const markRead = (id: number) =>
  apiClient.patch(`/notifications/${id}/read`)

export const markAllRead = () =>
  apiClient.patch('/notifications/read-all')

export const deleteNotification = (id: number) =>
  apiClient.delete(`/notifications/${id}`)
