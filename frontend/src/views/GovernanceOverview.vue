<template>
  <div class="governance-overview">
    <div v-if="!communityStore.currentCommunityId" class="empty-state">
      <el-empty description="请先选择一个社区" :image-size="150">
        <p class="empty-tip">使用顶部的社区切换器选择要管理的社区</p>
      </el-empty>
    </div>

    <template v-else>
      <!-- Page Header -->
      <div class="page-title">
        <div>
          <h2>社区治理</h2>
          <p class="subtitle">委员会运作 · 会议管理 · 成员协同</p>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.committeeCount }}</div>
            <div class="stat-label">活跃委员会</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.upcomingMeetings }}</div>
            <div class="stat-label">待召开会议</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.memberCount }}</div>
            <div class="stat-label">参与成员</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalMeetings }}</div>
            <div class="stat-label">历史会议</div>
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-content">
        <!-- Two Column Layout -->
        <div class="content-columns">
          <!-- Left Column: Committees -->
          <section class="content-card committees-card">
            <div class="card-header">
              <div class="card-title-group">
                <h2 class="card-title">委员会概览</h2>
                <span class="card-count">{{ committees.length }} / {{ stats.committeeCount }}</span>
              </div>
              <button class="card-action" @click="$router.push('/committees')">
                <span>查看全部</span>
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>

            <div v-loading="loadingCommittees" class="card-content">
              <div
                v-for="(committee, index) in committees"
                :key="committee.id"
                class="committee-item"
                :style="{ animationDelay: `${index * 40}ms` }"
                @click="$router.push('/committees/' + committee.id)"
              >
                <div class="committee-visual">
                  <div class="committee-avatar">
                    {{ committee.name.charAt(0).toUpperCase() }}
                  </div>
                  <div class="committee-badge"></div>
                </div>
                <div class="committee-details">
                  <h3 class="committee-name">{{ committee.name }}</h3>
                  <div class="committee-stats">
                    <span class="stat-item">
                      <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                      </svg>
                      {{ committee.member_count }} 成员
                    </span>
                    <span v-if="committee.is_active" class="stat-item active">
                      <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>
                      活跃中
                    </span>
                    <span v-else class="stat-item archived">已归档</span>
                  </div>
                </div>
                <svg class="committee-chevron" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
              <div v-if="committees.length === 0" class="empty-state-small">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                </svg>
                <p>暂无活跃委员会</p>
              </div>
            </div>
          </section>

          <!-- Right Column: Meetings -->
          <section class="content-card meetings-card">
            <div class="card-header">
              <div class="card-title-group">
                <h2 class="card-title">近期会议</h2>
                <span class="card-count">未来30天</span>
              </div>
              <button class="card-action" @click="$router.push('/meetings')">
                <span>会议日历</span>
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>

            <div v-loading="loadingMeetings" class="card-content">
              <div
                v-for="(meeting, index) in upcomingMeetings"
                :key="meeting.id"
                class="meeting-item"
                :style="{ animationDelay: `${index * 40}ms` }"
                @click="$router.push('/meetings/' + meeting.id)"
              >
                <div class="meeting-visual">
                  <div class="meeting-calendar">
                    <div class="calendar-month">{{ formatMonth(meeting.scheduled_at) }}</div>
                    <div class="calendar-day">{{ formatDay(meeting.scheduled_at) }}</div>
                  </div>
                </div>
                <div class="meeting-details">
                  <h3 class="meeting-title">{{ meeting.title }}</h3>
                  <div class="meeting-meta">
                    <span class="meta-time">
                      <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                      </svg>
                      {{ formatTime(meeting.scheduled_at) }}
                    </span>
                    <span class="meta-status" :class="meetingStatusClass(meeting.status)">
                      <span class="status-dot" :class="meetingDotClass(meeting.status)"></span>
                      {{ getMeetingStatusText(meeting.status) }}
                    </span>
                  </div>
                </div>
                <svg class="meeting-chevron" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
              <div v-if="upcomingMeetings.length === 0" class="empty-state-small">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
                </svg>
                <p>暂无即将召开的会议</p>
              </div>
            </div>
          </section>
        </div>

        <!-- Quick Actions Bar -->
        <section v-if="isAdmin" class="actions-bar">
          <div class="actions-content">
            <div class="actions-info">
              <svg class="actions-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              <div>
                <h3 class="actions-title">快捷操作</h3>
                <p class="actions-subtitle">创建新的委员会或安排会议</p>
              </div>
            </div>
            <div class="actions-buttons">
              <button class="action-btn btn-committees" @click="$router.push('/committees?action=create')">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                </svg>
                <span>创建委员会</span>
              </button>
              <button class="action-btn btn-meetings" @click="$router.push('/meetings?action=create')">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
                </svg>
                <span>安排会议</span>
              </button>
            </div>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listCommittees, listMeetings, type Committee, type Meeting } from '@/api/governance'
import { useUserStore } from '@/stores/user'
import { useCommunityStore } from '@/stores/community'

const router = useRouter()
const userStore = useUserStore()
const communityStore = useCommunityStore()
const isAdmin = computed(() => userStore.isCommunityAdmin)
const loadingCommittees = ref(false)
const loadingMeetings = ref(false)
const committees = ref<Committee[]>([])
const upcomingMeetings = ref<Meeting[]>([])

const stats = computed(() => {
  const now = new Date()
  const upcoming = upcomingMeetings.value.filter(
    m => new Date(m.scheduled_at) > now && m.status === 'scheduled'
  )
  return {
    committeeCount: committees.value.filter(c => c.is_active).length,
    memberCount: committees.value.reduce((sum, c) => sum + c.member_count, 0),
    upcomingMeetings: upcoming.length,
    totalMeetings: upcomingMeetings.value.length
  }
})

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadData()
  }
})

watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) {
      loadData()
    }
  }
)

async function loadData() {
  await Promise.all([loadCommittees(), loadMeetings()])
}

async function loadCommittees() {
  loadingCommittees.value = true
  try {
    const data = await listCommittees({ is_active: true })
    committees.value = data.slice(0, 5)
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会失败')
  } finally {
    loadingCommittees.value = false
  }
}

async function loadMeetings() {
  loadingMeetings.value = true
  try {
    const now = new Date()
    const startDate = now.toISOString().split('T')[0]
    const endDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    const data = await listMeetings({ start_date: startDate, end_date: endDate, limit: 5 })
    upcomingMeetings.value = data
  } catch (error: any) {
    ElMessage.error(error.message || '加载会议失败')
  } finally {
    loadingMeetings.value = false
  }
}

function formatDay(dateStr: string) {
  const date = new Date(dateStr)
  return date.getDate().toString().padStart(2, '0')
}

function formatMonth(dateStr: string) {
  const date = new Date(dateStr)
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  return months[date.getMonth()]
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function meetingDotClass(status: string) {
  const map: Record<string, string> = { 
    scheduled: 'indicator-scheduled', 
    in_progress: 'indicator-progress', 
    completed: 'indicator-completed', 
    cancelled: 'indicator-cancelled' 
  }
  return map[status] || 'indicator-scheduled'
}

function meetingStatusClass(status: string) {
  const map: Record<string, string> = { 
    scheduled: 'status-scheduled', 
    in_progress: 'status-progress', 
    completed: 'status-completed', 
    cancelled: 'status-cancelled' 
  }
  return map[status] || 'status-scheduled'
}

function getMeetingStatusText(status: string) {
  const map: Record<string, string> = { 
    scheduled: '已安排', 
    in_progress: '进行中', 
    completed: '已完成', 
    cancelled: '已取消' 
  }
  return map[status] || status
}
</script>

<style scoped>
/* LFX Insights Light Theme - Governance Overview */

.governance-overview {
  /* LFX Design Tokens - Light Theme */
  --bg-page: #f5f7fa;
  --bg-card: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;
  
  background: var(--bg-page);
  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Page Header */
.page-title {
  margin-bottom: 28px;
}

.page-title h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px;
  letter-spacing: -0.02em;
}

.page-title .subtitle {
  color: var(--text-secondary);
  font-size: 15px;
  margin: 0;
}

/* Empty State */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 60px 24px;
}

.empty-tip {
  color: var(--text-secondary);
  font-size: 15px;
  margin-top: 12px;
  text-align: center;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-hover);
}

.stat-icon {
  width: 40px;
  height: 40px;
  background: #eff6ff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--blue);
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Main Content */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
}

.content-columns {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* Content Cards */
.content-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.content-card:hover {
  box-shadow: var(--shadow-hover);
}

.card-header {
  padding: 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-page);
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-page);
  padding: 4px 10px;
  border-radius: 6px;
}

.card-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--blue);
  background: transparent;
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.card-action:hover {
  background: #eff6ff;
}

.card-action svg {
  width: 14px;
  height: 14px;
  transition: transform 0.2s ease;
}

.card-action:hover svg {
  transform: translateX(2px);
}

.card-content {
  padding: 8px;
  min-height: 300px;
}

/* Committee Items */
.committee-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  margin: 4px 0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.committee-item:hover {
  background: var(--bg-page);
  border-color: var(--border);
}

.committee-avatar {
  width: 44px;
  height: 44px;
  background: var(--blue);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.committee-badge {
  display: none;
}

.committee-details {
  flex: 1;
  min-width: 0;
}

.committee-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.committee-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-item svg {
  width: 14px;
  height: 14px;
}

.stat-item.active {
  color: var(--green);
  background: #f0fdf4;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.stat-item.archived {
  color: var(--text-muted);
  background: var(--bg-page);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
}

.committee-chevron {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.committee-item:hover .committee-chevron {
  transform: translateX(2px);
  color: var(--text-secondary);
}

/* Meeting Items */
.meeting-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  margin: 4px 0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.meeting-item:hover {
  background: var(--bg-page);
  border-color: var(--border);
}

.meeting-calendar {
  width: 48px;
  height: 48px;
  background: var(--blue);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.calendar-month {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

.calendar-day {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.meeting-details {
  flex: 1;
  min-width: 0;
}

.meeting-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.meeting-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-time svg {
  width: 14px;
  height: 14px;
}

.meta-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.meta-status.status-scheduled {
  background: #eff6ff;
  color: var(--blue);
}

.meta-status.status-scheduled .status-dot {
  background: var(--blue);
}

.meta-status.status-progress {
  background: #fffbeb;
  color: var(--orange);
}

.meta-status.status-progress .status-dot {
  background: var(--orange);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { 
    opacity: 1;
    transform: scale(1);
  }
  50% { 
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.meta-status.status-completed {
  background: #f0fdf4;
  color: var(--green);
}

.meta-status.status-completed .status-dot {
  background: var(--green);
}

.meta-status.status-cancelled {
  background: #f1f5f9;
  color: var(--text-muted);
}

.meta-status.status-cancelled .status-dot {
  background: var(--text-muted);
}

.indicator-scheduled .status-dot,
.indicator-progress .status-dot,
.indicator-completed .status-dot,
.indicator-cancelled .status-dot { 
  display: none; 
}

.meeting-chevron {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.meeting-item:hover .meeting-chevron {
  transform: translateX(2px);
  color: var(--text-secondary);
}

/* Empty State */
.empty-state-small {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 24px;
  color: var(--text-muted);
}

.empty-state-small svg {
  width: 48px;
  height: 48px;
  opacity: 0.3;
  margin-bottom: 16px;
  color: var(--text-muted);
}

.empty-state-small p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

/* Actions Bar */
.actions-bar {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
  margin-top: 32px;
}

.actions-bar:hover {
  box-shadow: var(--shadow-hover);
}

.actions-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.actions-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.actions-icon {
  width: 48px;
  height: 48px;
  background: var(--blue);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.actions-icon svg {
  width: 24px;
  height: 24px;
}

.actions-text {
  flex: 1;
}

.actions-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.actions-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.actions-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
}

.action-btn:hover svg {
  transform: translateX(2px);
}

.btn-committees {
  background: var(--blue);
  color: white;
}

.btn-committees:hover {
  background: #0077cc;
  box-shadow: var(--shadow-hover);
}

.btn-meetings {
  background: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.btn-meetings:hover {
  background: var(--bg-card);
  border-color: var(--blue);
}

/* Responsive Design */
@media (max-width: 1068px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-columns {
    gap: 16px;
  }
}

@media (max-width: 734px) {
  .governance-overview {
    padding: 24px 20px 48px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .content-columns {
    grid-template-columns: 1fr;
  }

  .card-header {
    padding: 20px;
  }

  .card-title {
    font-size: 16px;
  }

  .actions-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .actions-info {
    width: 100%;
  }

  .actions-buttons {
    width: 100%;
  }

  .action-btn {
    flex: 1;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .governance-overview {
    padding: 20px 16px 40px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .card-header {
    padding: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .card-action {
    width: 100%;
    justify-content: center;
  }

  .committee-item,
  .meeting-item {
    padding: 12px;
  }

  .actions-bar {
    padding: 20px 16px;
  }

  .actions-buttons {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
  }
}

/* Loading State */
:deep(.el-loading-mask) {
  background: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner .circular) {
  stroke: var(--blue);
  stroke-width: 3;
}
</style>
