import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  type Notification,
  getNotifications,
  getUnreadCount,
  markRead,
  markAllRead,
  deleteNotification,
} from '../api/notifications'

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  let pollTimer: number | null = null

  async function fetchUnreadCount() {
    try {
      const { count } = await getUnreadCount()
      unreadCount.value = count
    } catch {
      // 静默失败，不影响页面
    }
  }

  async function fetchNotifications(unreadOnly = false) {
    loading.value = true
    try {
      const data = await getNotifications({ unread_only: unreadOnly, limit: 30 })
      notifications.value = data.items
      unreadCount.value = data.unread_count
    } catch {
      // 静默失败
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(id: number) {
    try {
      await markRead(id)
      const notif = notifications.value.find(n => n.id === id)
      if (notif) {
        notif.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {
      // 静默失败
    }
  }

  async function markAllAsRead() {
    try {
      await markAllRead()
      notifications.value.forEach(n => { n.is_read = true })
      unreadCount.value = 0
    } catch {
      // 静默失败
    }
  }

  async function remove(id: number) {
    try {
      await deleteNotification(id)
      const idx = notifications.value.findIndex(n => n.id === id)
      if (idx !== -1) {
        const wasUnread = !notifications.value[idx].is_read
        notifications.value.splice(idx, 1)
        if (wasUnread) unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {
      // 静默失败
    }
  }

  function startPolling() {
    fetchUnreadCount()
    if (pollTimer === null) {
      pollTimer = window.setInterval(fetchUnreadCount, 30_000)
    }
  }

  function stopPolling() {
    if (pollTimer !== null) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    notifications.value = []
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    loading,
    fetchUnreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    remove,
    startPolling,
    stopPolling,
  }
})
