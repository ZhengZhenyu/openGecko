<template>
  <!-- 未登录页面（登录、忘记密码、重置密码、初始设置）：无侧边栏和顶栏 -->
  <div v-if="!showLayout" class="fullscreen-container">
    <router-view />
  </div>

  <!-- 已登录页面：带侧边栏和顶栏 -->
  <el-container v-else class="app-container">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="app-aside" :class="{ collapsed: sidebarCollapsed }">
      <div class="logo">
        <img v-if="!sidebarCollapsed" src="/openGecko-Horizontal.png" alt="openGecko" class="logo-img" />
        <img v-else src="/openGecko.jpg" alt="openGecko" class="logo-icon" />
      </div>
      <el-menu
        :default-active="route.path"
        router
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        background-color="#ffffff"
        text-color="#64748b"
        active-text-color="#0095ff"
      >
        <!-- 社区工作台 -->
        <el-menu-item index="/community">
          <el-icon><House /></el-icon>
          <span>社区工作台</span>
        </el-menu-item>

        <!-- 个人中心 -->
        <el-sub-menu index="personal">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>个人中心</span>
          </template>
          <el-menu-item index="/my-work">
            <el-icon><Checked /></el-icon>
            <span>工作看板</span>
          </el-menu-item>
          <el-menu-item index="/profile">
            <el-icon><Setting /></el-icon>
            <span>个人设置</span>
          </el-menu-item>
        </el-sub-menu>

        <el-divider style="margin: 8px 0" />

        <!-- 社区治理 -->
        <el-sub-menu index="governance">
          <template #title>
            <el-icon><Stamp /></el-icon>
            <span>社区治理</span>
          </template>
          <el-menu-item index="/community-overview">
            <el-icon><OfficeBuilding /></el-icon>
            <span>社区总览</span>
          </el-menu-item>
          <el-menu-item index="/governance">
            <el-icon><DataLine /></el-icon>
            <span>治理概览</span>
          </el-menu-item>
          <el-menu-item index="/committees">
            <el-icon><Avatar /></el-icon>
            <span>委员会</span>
          </el-menu-item>
          <el-menu-item index="/meetings">
            <el-icon><Calendar /></el-icon>
            <span>会议管理</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 内容管理 -->
        <el-sub-menu index="content">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>内容管理</span>
          </template>
          <el-menu-item index="/contents">
            <el-icon><List /></el-icon>
            <span>内容列表</span>
          </el-menu-item>
          <el-menu-item index="/content-calendar">
            <el-icon><Calendar /></el-icon>
            <span>内容日历</span>
          </el-menu-item>
          <el-menu-item index="/publish">
            <el-icon><Promotion /></el-icon>
            <span>发布渠道</span>
          </el-menu-item>
          <el-menu-item index="/wechat-stats">
            <el-icon><TrendCharts /></el-icon>
            <span>微信阅读统计</span>
          </el-menu-item>
          <el-menu-item index="/analytics">
            <el-icon><DataLine /></el-icon>
            <span>内容分析</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 活动管理 -->
        <el-sub-menu index="events">
          <template #title>
            <el-icon><Flag /></el-icon>
            <span>活动管理</span>
          </template>
          <el-menu-item index="/events">
            <el-icon><List /></el-icon>
            <span>社区活动</span>
          </el-menu-item>
          <el-menu-item index="/event-templates">
            <el-icon><Document /></el-icon>
            <span>SOP 模板</span>
          </el-menu-item>
          <el-menu-item index="/campaigns">
            <el-icon><MagicStick /></el-icon>
            <span>Campaign规划</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 洞察与人脉（可选模块） -->
        <el-sub-menu v-if="featuresStore.insightsModule" index="insights">
          <template #title>
            <el-icon><Connection /></el-icon>
            <span>洞察与人脉</span>
          </template>
          <el-menu-item index="/insights">
            <el-icon><TrendCharts /></el-icon>
            <span>洞察仪表板</span>
          </el-menu-item>
          <el-menu-item index="/people">
            <el-icon><UserFilled /></el-icon>
            <span>人脉管理</span>
          </el-menu-item>
          <el-menu-item index="/ecosystem">
            <el-icon><Share /></el-icon>
            <span>生态项目</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 平台管理（管理员及超管可见） -->
        <template v-if="isSuperuser || isAdminInCurrentCommunity">
          <el-divider style="margin: 8px 0" />
          <el-sub-menu index="platform">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>平台管理</span>
            </template>
            <el-menu-item v-if="!isSuperuser" index="/community-settings">
              <el-icon><Setting /></el-icon>
              <span>社区设置</span>
            </el-menu-item>
            <template v-if="isSuperuser">
              <el-menu-item index="/communities">
                <el-icon><Setting /></el-icon>
                <span>社区管理</span>
              </el-menu-item>
              <el-menu-item index="/users">
                <el-icon><User /></el-icon>
                <span>用户管理</span>
              </el-menu-item>
              <el-menu-item index="/workload">
                <el-icon><TrendCharts /></el-icon>
                <span>工作量总览</span>
              </el-menu-item>
              <el-menu-item index="/audit-logs">
                <el-icon><List /></el-icon>
                <span>审计日志</span>
              </el-menu-item>
            </template>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>
    <!-- 收缩切换按钮（悬浮在侧边栏右侧边缘） -->
    <button
      class="sidebar-toggle"
      :style="{ left: (sidebarCollapsed ? 64 : 220) - 12 + 'px' }"
      @click="toggleSidebar"
      :title="sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
    >
      <svg v-if="sidebarCollapsed" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
    </button>
    <el-container>
      <el-header class="app-header">
        <community-switcher v-if="showCommunitySwitcher" />
        <div class="header-right">
          <!-- 通知铃铛 -->
          <el-popover
            v-model:visible="notifPopoverVisible"
            placement="bottom-end"
            :width="360"
            trigger="click"
            @show="onBellClick"
          >
            <template #reference>
              <div class="notif-bell" :class="{ 'has-unread': notifStore.unreadCount > 0 }">
                <el-icon size="18"><Bell /></el-icon>
                <span v-if="notifStore.unreadCount > 0" class="notif-badge">
                  {{ notifStore.unreadCount > 99 ? '99+' : notifStore.unreadCount }}
                </span>
              </div>
            </template>
            <div class="notif-panel">
              <div class="notif-panel-header">
                <span class="notif-panel-title">通知</span>
                <el-button text size="small" @click="onMarkAllRead">全部已读</el-button>
              </div>
              <div v-if="notifStore.loading" class="notif-panel-empty">
                <el-icon class="is-loading"><Loading /></el-icon>
              </div>
              <div v-else-if="notifStore.notifications.length === 0" class="notif-panel-empty">暂无通知</div>
              <div v-else class="notif-list">
                <div
                  v-for="n in notifStore.notifications"
                  :key="n.id"
                  class="notif-item"
                  :class="{ unread: !n.is_read }"
                  @click="onNotifClick(n)"
                >
                  <div class="notif-item-dot" v-if="!n.is_read"></div>
                  <div class="notif-item-content">
                    <div class="notif-item-title">{{ n.title }}</div>
                    <div v-if="n.body" class="notif-item-body">{{ n.body }}</div>
                    <div class="notif-item-time">{{ formatAgo(n.created_at) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-popover>

          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ user?.username || '用户' }}</span>
              <el-tag v-if="isSuperuser" size="small" type="danger" style="margin-left: 6px">超级管理员</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>{{ user?.email }}</el-dropdown-item>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document, Promotion, Setting, Tools,
  OfficeBuilding, UserFilled, User, Stamp, DataLine, Avatar,
  Calendar, List, Checked, TrendCharts, House,
  Flag, Connection, MagicStick, Share, Bell, Loading,
} from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'
import { useCommunityStore } from './stores/community'
import { useFeaturesStore } from './stores/features'
import { useNotificationStore } from './stores/notifications'
import { getUserInfo } from './api/auth'
import CommunitySwitcher from './components/CommunitySwitcher.vue'
import type { Notification } from './api/notifications'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()
const featuresStore = useFeaturesStore()
const notifStore = useNotificationStore()

// 通知面板
const notifPopoverVisible = ref(false)

function onBellClick() {
  notifStore.fetchNotifications()
}

function formatAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  return `${days} 天前`
}

function onNotifClick(n: Notification) {
  notifStore.markAsRead(n.id)
  notifPopoverVisible.value = false
  if (n.resource_type === 'meeting' && n.resource_id) {
    router.push(`/meetings/${n.resource_id}`)
  } else if (n.resource_type === 'event_task') {
    router.push('/events')
  }
}

function onMarkAllRead() {
  notifStore.markAllAsRead()
}

const user = computed(() => authStore.user)
const isSuperuser = computed(() => authStore.isSuperuser)

// 侧边栏收缩状态（持久化到 localStorage）
const sidebarCollapsed = ref(localStorage.getItem('sidebar_collapsed') === 'true')
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar_collapsed', String(sidebarCollapsed.value))
}
const isAdminInCurrentCommunity = computed(() => {
  const cid = communityStore.currentCommunityId
  return cid ? authStore.isAdminInCommunity(cid) : false
})

// 判断是否显示侧边栏和顶栏布局
// 登录页、初始设置页、忘记密码页、重置密码页不显示
const showLayout = computed(() => {
  const noLayoutRoutes = ['Login', 'InitialSetup', 'ForgotPassword', 'ResetPassword']
  return !noLayoutRoutes.includes(route.name as string)
})

// 判断是否显示社区选择下拉框
// 仅在需要社区上下文的页面（社区工作台、社区治理）显示
const showCommunitySwitcher = computed(() => {
  const showSwitcherRoutes = [
    'CommunitySandbox',
    'GovernanceOverview',
    'CommitteeList',
    'CommitteeDetail',
    'CommitteeMemberManage',
    'MeetingCalendar',
    'MeetingDetail',
    'CommunitySettings',
  ]
  return showSwitcherRoutes.includes(route.name as string)
})

onMounted(async () => {
  if (authStore.isAuthenticated) {
    notifStore.startPolling()
    // Always fetch user info and communities to ensure they're up to date
    if (!authStore.user || authStore.communities.length === 0) {
      try {
        const userInfo = await getUserInfo()
        authStore.setUser(userInfo.user)
        authStore.setCommunities(userInfo.communities)
        
        // Set the first community as default if not already set
        if (userInfo.communities.length > 0) {
          const currentCommunityId = localStorage.getItem('current_community_id')
          if (!currentCommunityId) {
            localStorage.setItem('current_community_id', String(userInfo.communities[0].id))
          }
        }
      } catch {
        // If failed to get user info, clear auth
      }
    }
  }
})

function handleCommand(command: string) {
  if (command === 'logout') {
    notifStore.stopPolling()
    authStore.clearAuth()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #1e293b;
}

/* 全局：节假日事件条带 — 完全由 renderHolidayContent 提供视觉，清除 FullCalendar 所有默认样式 */
.fc-event.holiday-publicHoliday,
.fc-event.holiday-traditional,
.fc-h-event.holiday-publicHoliday,
.fc-h-event.holiday-traditional,
.fc-daygrid-event.holiday-publicHoliday,
.fc-daygrid-event.holiday-traditional,
.fc-daygrid-block-event.holiday-publicHoliday,
.fc-daygrid-block-event.holiday-traditional {
  --fc-event-bg-color: transparent;
  --fc-event-border-color: transparent;
  --fc-event-text-color: transparent;
  background-color: transparent !important;
  background: transparent !important;
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 0 !important;
}
.fc-event.holiday-publicHoliday::before,
.fc-event.holiday-publicHoliday::after,
.fc-event.holiday-traditional::before,
.fc-event.holiday-traditional::after {
  display: none !important;
  content: none !important;
}
.fc-event.holiday-publicHoliday .fc-event-main,
.fc-event.holiday-traditional .fc-event-main {
  padding: 0 !important;
  height: 100% !important;
}
/* 隐藏节假日事件的 FullCalendar 拖拽/缩放手柄（含 hover 态，提高优先级压过 FC 自身规则） */
.fc .fc-event.holiday-publicHoliday .fc-event-resizer,
.fc .fc-event.holiday-traditional .fc-event-resizer,
.fc .fc-event.holiday-publicHoliday:hover .fc-event-resizer,
.fc .fc-event.holiday-traditional:hover .fc-event-resizer,
.fc .fc-event-selected.holiday-publicHoliday .fc-event-resizer,
.fc .fc-event-selected.holiday-traditional .fc-event-resizer {
  display: none !important;
  visibility: hidden !important;
  width: 0 !important;
  pointer-events: none !important;
}
.fc .fc-event.holiday-publicHoliday:hover,
.fc .fc-event.holiday-traditional:hover {
  opacity: 1 !important;
  filter: none !important;
}

.fullscreen-container {
  width: 100%;
  height: 100vh;
  overflow: auto;
}

.app-container {
  height: 100vh;
}

.app-aside {
  background-color: #ffffff;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid #e2e8f0;
  transition: width 0.22s ease;
  display: flex;
  flex-direction: column;
  position: relative;
}

.app-aside::-webkit-scrollbar {
  width: 4px;
}

.app-aside::-webkit-scrollbar-track {
  background: transparent;
}

.app-aside::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  min-height: 64px;
  flex-shrink: 0;
}

.logo-img {
  width: 100%;
  max-width: 180px;
  height: auto;
}

.logo-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s ease;
}

.user-info:hover {
  color: #0095ff;
}

/* ── 通知铃铛 ─────────────────────────── */
.notif-bell {
  position: relative;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.notif-bell:hover {
  background: #f1f5f9;
  color: #1e293b;
}
.notif-bell.has-unread {
  color: #0095ff;
}
.notif-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  line-height: 16px;
  text-align: center;
}

/* ── 通知面板 ─────────────────────────── */
.notif-panel {
  padding: 0;
}
.notif-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px 8px;
  border-bottom: 1px solid #f1f5f9;
}
.notif-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}
.notif-panel-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
  color: #94a3b8;
  font-size: 13px;
  gap: 6px;
}
.notif-list {
  max-height: 320px;
  overflow-y: auto;
}
.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f8fafc;
  transition: background 0.12s;
}
.notif-item:hover {
  background: #f8fafc;
}
.notif-item.unread {
  background: #eff6ff;
}
.notif-item.unread:hover {
  background: #dbeafe;
}
.notif-item-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #0095ff;
  margin-top: 6px;
}
.notif-item-content {
  flex: 1;
  min-width: 0;
}
.notif-item-title {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.notif-item-body {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.notif-item-time {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 4px;
}

.app-main {
  background-color: #f5f7fa;
  overflow-y: auto;
  padding: 0;
}

.el-menu {
  border-right: none !important;
  flex: 1;
}

/* 取消 el-menu collapse 模式的固定宽度限制 */
.app-aside.collapsed .el-menu--collapse {
  width: 64px !important;
}

/* 收缩切换按钮（悬浮右边缘圆形按钮） */
.sidebar-toggle {
  position: fixed;
  top: 72px;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.10);
  cursor: pointer;
  color: #94a3b8;
  padding: 0;
  transition: left 0.22s ease, color 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.sidebar-toggle:hover {
  color: #0095ff;
  border-color: #0095ff;
  box-shadow: 0 2px 8px rgba(0, 149, 255, 0.18);
}

/* LFX-style sidebar menu items */
.app-aside .el-menu-item {
  border-radius: 8px;
  margin: 2px 8px;
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.app-aside .el-menu-item:hover {
  background-color: #f8fafc !important;
  color: #1e293b !important;
}

.app-aside .el-menu-item.is-active {
  background-color: #eff6ff !important;
  color: #0095ff !important;
}

.app-aside .el-sub-menu .el-sub-menu__title {
  border-radius: 8px;
  margin: 2px 8px;
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  font-weight: 500;
}

.app-aside .el-sub-menu .el-sub-menu__title:hover {
  background-color: #f8fafc !important;
}

.app-aside .el-sub-menu .el-sub-menu__title {
  color: #64748b !important;
}

.app-aside .el-sub-menu.is-active .el-sub-menu__title {
  color: #0095ff !important;
}

.app-aside .el-sub-menu .el-menu-item {
  padding-left: 52px !important;
  margin: 1px 8px;
  height: 38px;
  line-height: 38px;
  font-size: 13px;
}
</style>
