<template>
  <div class="sandbox">
    <!-- 空状态：未加入任何社区 -->
    <div v-if="authStore.communities.length === 0" class="empty-state">
      <el-empty description="您还没有加入任何社区" :image-size="200">
        <template v-if="authStore.isSuperuser">
          <p class="empty-tip">作为超级管理员，您可以创建社区开始使用</p>
          <el-button type="primary" @click="$router.push('/community-wizard')">创建社区</el-button>
        </template>
        <template v-else>
          <p class="empty-tip">请联系管理员将您添加到社区</p>
        </template>
      </el-empty>
    </div>

    <!-- 空状态：已有社区但未选择 -->
    <div v-else-if="!communityStore.currentCommunityId" class="empty-state">
      <el-empty description="请先选择一个社区" :image-size="150">
        <p class="empty-tip">使用顶部的社区切换器选择要管理的社区</p>
      </el-empty>
    </div>

    <!-- 正常工作台 -->
    <div v-else>
      <!-- 社区 Header -->
      <div class="community-header">
        <div class="community-info">
          <div v-if="currentCommunity?.logo_url" class="community-logo">
            <img :src="currentCommunity.logo_url" :alt="currentCommunity.name" />
          </div>
          <div v-else class="community-logo-placeholder">
            {{ currentCommunity?.name?.charAt(0)?.toUpperCase() }}
          </div>
          <div class="community-text">
            <h1 class="community-name">{{ currentCommunity?.name }}</h1>
            <p class="community-desc">{{ currentCommunity?.description || '暂无描述' }}</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="$router.push('/contents/new')">
            <el-icon><Plus /></el-icon> 新建内容
          </el-button>
          <el-button type="primary" size="small" @click="$router.push('/events/new')">
            <el-icon><Calendar /></el-icon> 创建活动
          </el-button>
        </div>
      </div>

      <!-- 加载骨架屏 -->
      <div v-if="loading" class="skeleton-wrap">
        <el-skeleton :rows="3" animated />
      </div>

      <template v-else-if="dashboardData">
        <!-- 新社区引导横幅 -->
        <div v-if="isNewCommunity" class="onboarding-banner">
          <div class="onboarding-left">
            <span class="onboard-emoji">🎉</span>
            <div>
              <div class="onboard-title">社区刚刚创建，从这里开始!</div>
              <div class="onboard-desc">完成基础配置，让社区运转起来。</div>
            </div>
          </div>
          <div class="onboarding-right">
            <el-button
              v-if="authStore.isSuperuser"
              type="primary"
              size="small"
              @click="$router.push(`/community-settings/${communityStore.currentCommunityId}`)"
            >
              <el-icon><Setting /></el-icon> 配置社区
            </el-button>
            <el-button v-else size="small" disabled>请联系超管完成配置</el-button>
          </div>
        </div>
        <!-- 第一层：社区事件日历（全宽，置顶） -->
        <div class="section-card calendar-card">
          <div class="card-header">
            <h3>社区事件日历</h3>
            <div class="calendar-legend">
              <span class="legend-section-label">类型</span>
              <span class="legend-bar lb-meeting">会议</span>
              <span class="legend-bar lb-event">活动</span>
              <span class="legend-bar lb-content">内容</span>
              <span class="legend-divider"></span>
              <span class="legend-section-label">状态</span>
              <span class="legend-dot-item"><span class="legend-dot ld-purple"></span>策划中</span>
              <span class="legend-dot-item"><span class="legend-dot ld-blue"></span>进行中</span>
              <span class="legend-dot-item"><span class="legend-dot ld-green"></span>已完成/发布</span>
              <span class="legend-dot-item"><span class="legend-dot ld-orange"></span>已排期</span>
              <span class="legend-dot-item"><span class="legend-dot ld-gray"></span>已取消</span>
            </div>
          </div>
          <FullCalendar ref="calendarRef" :options="calendarOptions" class="ver-calendar" />
        </div>

        <!-- 第二层：治理 & 渠道指标 (3列) -->
        <div class="metrics-grid">
          <div class="metric-card" @click="$router.push('/governance')">
            <div class="metric-icon-wrap gov-icon">
              <el-icon><Stamp /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.total_committees }}</div>
              <div class="metric-label">委员会</div>
            </div>
          </div>
          <div class="metric-card highlight-blue" @click="$router.push('/meetings')">
            <div class="metric-icon-wrap meeting-icon">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.upcoming_meetings }}</div>
              <div class="metric-label">即将会议</div>
            </div>
          </div>
          <div class="metric-card" @click="$router.push('/settings')">
            <div class="metric-icon-wrap channel-icon">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.active_channels }}</div>
              <div class="metric-label">活跃渠道</div>
            </div>
          </div>
        </div>

        <!-- 第三层：内容动态（按状态分组） -->
        <div class="section-card content-status-card">
          <div class="card-header">
            <div class="content-tabs">
              <button
                v-for="tab in contentTabs"
                :key="tab.key"
                class="content-tab"
                :class="{ active: contentTab === tab.key }"
                @click="contentTab = tab.key"
              >
                {{ tab.label }}
                <span class="tab-count">{{ contentCountByStatus(tab.key) }}</span>
              </button>
            </div>
            <router-link :to="`/contents?status=${contentTab}`" class="view-all">查看全部 →</router-link>
          </div>
          <div v-if="tabContents.length === 0" class="empty-hint">暂无{{ currentTabLabel }}内容</div>
          <el-table
            v-else
            :data="tabContents"
            style="width: 100%"
            size="small"
            @row-click="(row: any) => $router.push(`/contents/${row.id}/edit`)"
            class="dashboard-table"
          >
            <el-table-column label="标题" prop="title" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="table-link">{{ row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column label="负责人" prop="owner_name" width="100" show-overflow-tooltip />
            <el-table-column label="工作状态" width="90">
              <template #default="{ row }">
                <span v-if="row.work_status" class="status-badge" :class="workStatusClass(row.work_status)">
                  {{ workStatusLabel(row.work_status) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="日期" width="90">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 第四层：趋势图 + 渠道统计 -->
        <div class="charts-row">
          <div class="chart-card">
            <div class="card-header">
              <h3>内容发布趋势</h3>
              <span class="card-desc">近 6 个月</span>
            </div>
            <v-chart class="chart" :option="trendChartOption" autoresize />
          </div>
          <div class="chart-card">
            <div class="card-header">
              <h3>渠道发布统计</h3>
              <span class="card-desc">累计发布量</span>
            </div>
            <v-chart class="chart" :option="channelChartOption" autoresize />
          </div>
        </div>

        <!-- 第五层：近期活动 + 即将会议 -->
        <div class="bottom-row">
          <div class="section-card">
            <div class="card-header">
              <h3>近期活动</h3>
              <router-link to="/events" class="view-all">查看全部 →</router-link>
            </div>
            <div v-if="recentEvents.length === 0" class="empty-hint">暂无近期活动</div>
            <el-table
              v-else
              :data="recentEvents"
              style="width: 100%"
              size="small"
              @row-click="(row: any) => $router.push(`/events/${row.id}`)"
              class="dashboard-table"
            >
              <el-table-column label="活动名称" prop="title" min-width="140" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="table-link">{{ row.title }}</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <span class="status-badge" :class="eventStatusClass(row.status)">{{ eventStatusLabel(row.status) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="日期" width="90">
                <template #default="{ row }">{{ row.planned_at ? formatDate(row.planned_at) : '—' }}</template>
              </el-table-column>
            </el-table>
          </div>

          <div class="section-card">
            <div class="card-header">
              <h3>即将到来的会议</h3>
              <router-link to="/meetings" class="view-all">查看全部 →</router-link>
            </div>
            <div v-if="dashboardData.upcoming_meetings.length === 0" class="empty-hint">
              近期无会议安排
            </div>
            <el-table
              v-else
              :data="dashboardData.upcoming_meetings"
              style="width: 100%"
              size="small"
              @row-click="(row: any) => $router.push(`/meetings/${row.id}`)"
              class="dashboard-table"
            >
              <el-table-column label="时间" width="76">
                <template #default="{ row }">
                  <div class="meeting-cell-date">
                    <div class="mcd-day">{{ formatDay(row.scheduled_at) }}</div>
                    <div class="mcd-month">{{ formatMonth(row.scheduled_at) }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="会议名称" prop="title" min-width="130" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="table-link">{{ row.title }}</span>
                </template>
              </el-table-column>
              <el-table-column label="委员会" prop="committee_name" width="100" show-overflow-tooltip />
              <el-table-column label="开始时间" width="72">
                <template #default="{ row }">{{ formatTime(row.scheduled_at) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { CalendarOptions, EventContentArg } from '@fullcalendar/core'
import {
  Stamp, Calendar, Connection, Plus, Setting,
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'
import { getCommunityDashboard, type CommunityDashboardResponse } from '../api/communityDashboard'
import { listEvents, type EventListItem } from '../api/event'

// 按需注册 ECharts 组件（Tree Shaking）
use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent])

const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const loading = ref(false)
const dashboardData = ref<CommunityDashboardResponse | null>(null)
const calendarRef = ref()
const recentEvents = ref<EventListItem[]>([])

// Content status tabs
const contentTab = ref<string>('reviewing')
const contentTabs = [
  { key: 'reviewing', label: '待审核' },
  { key: 'draft',     label: '草稿' },
  { key: 'published', label: '近期发布' },
]
const tabContents = computed(() =>
  (dashboardData.value?.recent_contents ?? []).filter(c => c.status === contentTab.value)
)
const currentTabLabel = computed(() =>
  contentTabs.find(t => t.key === contentTab.value)?.label ?? ''
)
function contentCountByStatus(status: string) {
  return (dashboardData.value?.recent_contents ?? []).filter(c => c.status === status).length
}

// 当前激活社区信息
const currentCommunity = computed(() =>
  communityStore.currentCommunityId
    ? authStore.getCommunityById(communityStore.currentCommunityId)
    : null
)

// 当前用户在该社区是否为管理员
const isCurrentCommunityAdmin = computed(() =>
  communityStore.currentCommunityId
    ? authStore.isAdminInCommunity(communityStore.currentCommunityId)
    : false
)

// 是否是全新社区（需要展示引导横幅）
const isNewCommunity = computed(() => {
  if (!dashboardData.value) return false
  const m = dashboardData.value.metrics
  return (m.total_contents || 0) === 0
})

// ===== 数据加载 =====

async function loadDashboard() {
  if (!communityStore.currentCommunityId) return
  loading.value = true
  try {
    dashboardData.value = await getCommunityDashboard(communityStore.currentCommunityId)
  } catch (e) {
    console.error('Failed to load community dashboard', e)
  } finally {
    loading.value = false
  }
}

async function loadEvents() {
  if (!communityStore.currentCommunityId) return
  try {
    const res = await listEvents({ community_id: communityStore.currentCommunityId, page: 1, page_size: 6 })
    recentEvents.value = res.items
  } catch (e) {
    console.error('Failed to load events', e)
  }
}

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadDashboard()
    loadEvents()
  }
})

watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) {
      loadDashboard()
      loadEvents()
    } else {
      dashboardData.value = null
      recentEvents.value = []
    }
  }
)

// ===== 图表配置 =====

const trendChartOption = computed(() => {
  const months = dashboardData.value?.monthly_trend.map((t) => t.month) ?? []
  const counts = dashboardData.value?.monthly_trend.map((t) => t.count) ?? []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: 16, right: 16, bottom: 40, top: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 12 },
    },
    series: [
      {
        name: '发布数',
        type: 'line',
        data: counts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#0095ff', width: 2 },
        itemStyle: { color: '#0095ff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,149,255,0.18)' },
              { offset: 1, color: 'rgba(0,149,255,0)' },
            ],
          },
        },
      },
    ],
  }
})

const channelChartOption = computed(() => {
  const stats = dashboardData.value?.channel_stats
  const channels = ['微信公众号', 'Hugo 博客', 'CSDN', '知乎']
  const values = [
    stats?.wechat ?? 0,
    stats?.hugo ?? 0,
    stats?.csdn ?? 0,
    stats?.zhihu ?? 0,
  ]
  const colors = ['#10b981', '#0095ff', '#f59e0b', '#8b5cf6']
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 16, right: 24, bottom: 40, top: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: channels,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 12 },
    },
    series: [
      {
        name: '发布数',
        type: 'bar',
        data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: 4 } })),
        barMaxWidth: 48,
      },
    ],
  }
})

// ===== FullCalendar 配置 =====

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-cn',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  buttonText: { today: '今天' },
  height: 580,
  events: (dashboardData.value?.calendar_events ?? []).map((e, idx) => ({
    id: `${e.resource_type}_${e.resource_id}_${e.type}_${idx}`,
    title: e.title,
    date: e.date,
    color: 'transparent',
    textColor: 'transparent',
    extendedProps: { type: e.type, resource_id: e.resource_id, resource_type: e.resource_type, statusColor: e.color },
  })),
  eventContent: (arg: EventContentArg) => {
    const { type, statusColor } = arg.event.extendedProps as { type: string; statusColor: string; resource_id: number; resource_type: string }
    let barBg = '#f8fafc'
    let barText = '#64748b'
    let barAccent = '#94a3b8'  // 左边框颜色 = 类型色，与状态无关
    if (type?.startsWith('meeting')) { barBg = '#eff6ff'; barText = '#1d4ed8'; barAccent = '#1d4ed8' }
    else if (type?.startsWith('event')) { barBg = '#f5f3ff'; barText = '#6d28d9'; barAccent = '#6d28d9' }
    else { barBg = '#f0fdf4'; barText = '#15803d'; barAccent = '#15803d' }  // content
    const dotColor = statusColor || barAccent  // 圆点颜色 = 状态色
    const wrapper = document.createElement('div')
    wrapper.style.cssText = `display:flex;align-items:center;gap:4px;background:${barBg};border-left:3px solid ${barAccent};padding:1px 5px 1px 4px;border-radius:3px;width:100%;box-sizing:border-box;overflow:hidden;`
    const dot = document.createElement('span')
    dot.style.cssText = `width:6px;height:6px;border-radius:50%;background:${dotColor};flex-shrink:0;`
    const titleEl = document.createElement('span')
    titleEl.style.cssText = `font-size:11px;font-weight:500;color:${barText};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;`
    titleEl.textContent = arg.event.title
    wrapper.appendChild(dot)
    wrapper.appendChild(titleEl)
    return { domNodes: [wrapper] }
  },
  eventClick: (info) => {
    const { type, resource_id } = info.event.extendedProps
    if (type?.startsWith('meeting')) router.push(`/meetings/${resource_id}`)
    else if (type?.startsWith('event')) router.push(`/events/${resource_id}`)
    else if (type === 'publish') router.push(`/contents/${resource_id}/edit`)
    else if (type === 'scheduled') router.push(`/contents/${resource_id}/edit`)
  },
  dayMaxEvents: 3,
}))

// ===== 工具函数 =====

function statusLabel(s: string) {
  const m: Record<string, string> = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布' }
  return m[s] || s
}

function workStatusLabel(s: string | null) {
  const m: Record<string, string> = { planning: '计划中', in_progress: '进行中', completed: '已完成' }
  return s ? (m[s] || s) : ''
}

function workStatusClass(s: string) {
  const m: Record<string, string> = { planning: 'badge-gray', in_progress: 'badge-orange', completed: 'badge-green' }
  return m[s] || 'badge-gray'
}

function statusClass(s: string) {
  const m: Record<string, string> = {
    draft: 'badge-gray',
    reviewing: 'badge-orange',
    approved: 'badge-blue',
    published: 'badge-green',
  }
  return m[s] || 'badge-gray'
}

function eventStatusLabel(s: string) {
  const m: Record<string, string> = {
    planning: '策划中', ongoing: '进行中', completed: '已完成', cancelled: '已取消',
  }
  return m[s] || s
}

function eventStatusClass(s: string) {
  const m: Record<string, string> = {
    planning: 'badge-gray', ongoing: 'badge-blue', completed: 'badge-green', cancelled: 'badge-gray',
  }
  return m[s] || 'badge-gray'
}

function formatDate(dt: string) {
  return new Date(dt).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function formatDay(dt: string) {
  return new Date(dt).getDate()
}

function formatMonth(dt: string) {
  return new Date(dt).toLocaleDateString('zh-CN', { month: 'short' })
}

function formatTime(dt: string) {
  return new Date(dt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
/* ===== LFX Insights 浅色主题 CSS 变量 ===== */
.sandbox {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --dark-blue: #00347b;
  --green: #10b981;
  --orange: #f59e0b;
  --purple: #8b5cf6;
  --red: #ef4444;
  --bg-page: #f5f7fa;
  --bg-card: #ffffff;
  --border: #e2e8f0;
  --border-hover: #cbd5e1;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1280px;
  margin: 0 auto;
}

/* ===== 空状态 ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
.empty-tip {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 12px;
}

/* ===== 社区 Header ===== */
.community-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 12px;
}
.community-info {
  display: flex;
  align-items: center;
  gap: 16px;
}
.community-logo {
  width: 64px;
  height: 64px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  box-sizing: border-box;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.community-logo img {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  object-fit: contain;
}
.community-logo-placeholder {
  width: 64px;
  height: 64px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--blue), var(--dark-blue));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
}
.community-name {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.community-desc {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* ===== 新社区引导横幅 ===== */
.onboarding-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 14px 20px;
  margin-bottom: 20px;
}
.onboarding-left { display: flex; align-items: center; gap: 14px; }
.onboard-emoji { font-size: 28px; }
.onboard-title { font-size: 14px; font-weight: 600; color: #1e3a8a; }
.onboard-desc { font-size: 12px; color: #3b82f6; margin-top: 2px; }

/* ===== 骨架屏 ===== */
.skeleton-wrap {
  padding: 24px 0;
}

/* ===== 治理指标卡片网格 (3列) ===== */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow);
}
.metric-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: var(--blue);
  transform: translateY(-1px);
}
.metric-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.content-icon  { background: #eff6ff; color: var(--blue); }
.publish-icon  { background: #f0fdf4; color: var(--green); }
.review-icon   { background: #fffbeb; color: var(--orange); }
.draft-icon    { background: #f8fafc; color: var(--text-muted); }
.gov-icon      { background: #faf5ff; color: var(--purple); }
.member-icon   { background: #fff1f2; color: var(--red); }
.meeting-icon  { background: #eff6ff; color: var(--blue); }
.channel-icon  { background: #f0fdf4; color: var(--green); }

.metric-body {
  flex: 1;
  min-width: 0;
}
.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}
.metric-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.metric-card.highlight-green .metric-value { color: var(--green); }
.metric-card.highlight-orange .metric-value { color: var(--orange); }
.metric-card.highlight-blue .metric-value { color: var(--blue); }

/* ===== 图表行 ===== */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}
.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 20px 12px;
  box-shadow: var(--shadow);
}
.chart {
  height: 220px;
}

/* ===== 通用卡片 ===== */
.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.card-desc {
  font-size: 13px;
  color: var(--text-muted);
}
.view-all {
  font-size: 13px;
  color: var(--blue);
  text-decoration: none;
  font-weight: 500;
}
.view-all:hover { text-decoration: underline; }

/* ===== 日历卡片 ===== */
.calendar-card {
  margin-bottom: 24px;
}
.calendar-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.legend-section-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  white-space: nowrap;
  margin-right: 2px;
}
/* Legend: bar samples for type */
.legend-bar {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px 2px 5px;
  border-radius: 4px;
  border-left: 3px solid;
  white-space: nowrap;
}
.lb-meeting { background: #eff6ff; color: #1d4ed8; border-left-color: #1d4ed8; }
.lb-event   { background: #f5f3ff; color: #6d28d9; border-left-color: #6d28d9; }
.lb-content { background: #f0fdf4; color: #15803d; border-left-color: #15803d; }

/* Legend: dot + label samples for status */
.legend-dot-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ld-purple { background: #8b5cf6; }
.ld-blue   { background: #0095ff; }
.ld-green  { background: #10b981; }
.ld-orange { background: #f59e0b; }
.ld-gray   { background: #94a3b8; }

.legend-divider {
  width: 1px;
  height: 16px;
  background: #e2e8f0;
  margin: 0 4px;
}

/* ===== 内容动态卡片 ===== */
.content-status-card {
  margin-bottom: 20px;
}

.content-tabs {
  display: flex;
  gap: 4px;
}

.content-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.content-tab:hover {
  border-color: var(--blue);
  color: var(--blue);
}

.content-tab.active {
  background: #eff6ff;
  border-color: var(--blue);
  color: var(--blue);
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--border);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
}

.content-tab.active .tab-count {
  background: var(--blue);
  color: #fff;
}

/* ===== 底部两栏 ===== */
.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* ===== 底部表格样式 ===== */
.table-link {
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s;
}
.dashboard-table :deep(.el-table__row) {
  cursor: pointer;
}
.dashboard-table :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}
.dashboard-table :deep(.el-table__row:hover .table-link) {
  color: var(--blue);
}
.dashboard-table :deep(.el-table th) {
  background: #f8fafc;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border);
  padding: 8px 0;
}
.dashboard-table :deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
  padding: 8px 0;
}

/* 会议日期单元格 */
.meeting-cell-date {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  width: 36px;
  height: 38px;
  background: #eff6ff;
  border-radius: 7px;
  justify-content: center;
}
.mcd-day {
  font-size: 16px;
  font-weight: 700;
  color: var(--blue);
  line-height: 1;
}
.mcd-month {
  font-size: 9px;
  color: #60a5fa;
  font-weight: 600;
  margin-top: 1px;
}

/* Status badges */
.status-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 99px;
}
.badge-gray   { background: #f1f5f9; color: #64748b; }
.badge-orange { background: #fff7ed; color: #c2410c; }
.badge-blue   { background: #eff6ff; color: #1d4ed8; }
.badge-green  { background: #f0fdf4; color: #15803d; }

/* ===== 空提示 ===== */
.empty-hint {
  text-align: center;
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 14px;
}

/* ===== FullCalendar 深度样式 ===== */
:deep(.fc) {
  font-family: inherit;
}

/* 工具栏标题 */
:deep(.fc-toolbar) {
  margin-bottom: 16px !important;
  align-items: center !important;
}
:deep(.fc-toolbar-title) {
  font-size: 15px !important;
  font-weight: 700 !important;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

/* 所有按钮基础 */
:deep(.fc-button) {
  background: #fff !important;
  border: 1px solid var(--border) !important;
  color: var(--text-secondary) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 4px 10px !important;
  border-radius: 7px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
  transition: background 0.13s, border-color 0.13s, color 0.13s !important;
}
:deep(.fc-button:hover:not(:disabled)) {
  background: #f1f5f9 !important;
  border-color: #cbd5e1 !important;
  color: var(--text-primary) !important;
}
:deep(.fc-button.fc-button-active) {
  background: var(--blue) !important;
  border-color: var(--blue) !important;
  color: #fff !important;
  box-shadow: 0 2px 7px rgba(0,149,255,0.28) !important;
}
:deep(.fc-button:focus) { box-shadow: none !important; }

/* 今天按钮 */
:deep(.fc-today-button) {
  background: rgba(0,149,255,0.08) !important;
  border-color: rgba(0,149,255,0.22) !important;
  color: var(--blue) !important;
  font-weight: 600 !important;
  border-radius: 7px !important;
}
:deep(.fc-today-button:hover:not(:disabled)) {
  background: rgba(0,149,255,0.15) !important;
  border-color: var(--blue) !important;
}

/* 前/后翻页 */
:deep(.fc-prev-button),
:deep(.fc-next-button) {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  color: var(--text-muted) !important;
  padding: 4px 7px !important;
}
:deep(.fc-prev-button:hover:not(:disabled)),
:deep(.fc-next-button:hover:not(:disabled)) {
  background: #f1f5f9 !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

/* 视图切换胶囊 */
:deep(.fc-button-group) {
  background: #f1f5f9;
  border-radius: 9px;
  padding: 2px;
  gap: 1px;
}
:deep(.fc-button-group .fc-button) {
  border-radius: 7px !important;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 3px 10px !important;
  color: var(--text-secondary) !important;
}
:deep(.fc-button-group .fc-button:hover:not(:disabled)) {
  background: rgba(255,255,255,0.65) !important;
  color: var(--text-primary) !important;
}
:deep(.fc-button-group .fc-button.fc-button-active) {
  background: #fff !important;
  color: var(--blue) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.09) !important;
  border: none !important;
}

/* 表头星期行 */
:deep(.fc-col-header-cell) {
  background: #fff !important;
  border-color: transparent !important;
  padding: 8px 0 6px !important;
}
:deep(.fc-col-header-cell-cushion) {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  text-decoration: none !important;
}
:deep(.fc-col-header) {
  border-bottom: 2px solid #e2e8f0 !important;
}

/* 日期单元格 */
:deep(.fc-daygrid-day) {
  border-color: #f1f5f9 !important;
  transition: background 0.12s;
}
:deep(.fc-daygrid-day:hover:not(.fc-day-today)) {
  background: #fafbfc;
}
:deep(.fc-daygrid-day.fc-day-other .fc-daygrid-day-number) {
  color: #cbd5e1 !important;
}
:deep(.fc-daygrid-day-top) {
  justify-content: flex-end;
}

/* 今天单元格 */
:deep(.fc-day-today) {
  background: linear-gradient(145deg, rgba(0,149,255,0.07) 0%, rgba(0,149,255,0.01) 100%) !important;
}
:deep(.fc-day-today .fc-daygrid-day-number) {
  background: var(--blue) !important;
  color: #fff !important;
  border-radius: 14px !important;
  padding: 2px 8px !important;
  margin: 4px 5px !important;
  font-weight: 700 !important;
  white-space: nowrap !important;
  display: inline-block !important;
  line-height: 1.6 !important;
  box-sizing: border-box !important;
  box-shadow: 0 2px 7px rgba(0,149,255,0.32) !important;
}

/* 普通日期数字 */
:deep(.fc-daygrid-day-number) {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  padding: 4px 6px !important;
  text-decoration: none !important;
}

/* 事件胶囊 — 背景/边框由 eventContent 的 domNodes 控制 */
:deep(.fc-event) {
  border-radius: 4px !important;
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 3px 2px !important;
  cursor: pointer !important;
  transition: transform 0.11s, box-shadow 0.11s !important;
}
:deep(.fc-event:hover) {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0,0,0,0.12) !important;
}
:deep(.fc-event-main) {
  overflow: hidden;
  border-radius: 3px;
}

/* "更多"链接 */
:deep(.fc-daygrid-more-link) {
  font-size: 10px;
  font-weight: 600;
  color: var(--blue) !important;
  background: rgba(0,149,255,0.08);
  border-radius: 3px;
  padding: 1px 5px;
  text-decoration: none !important;
}

/* 周末轻染色 */
:deep(.fc-day-sat:not(.fc-day-today)),
:deep(.fc-day-sun:not(.fc-day-today)) {
  background: rgba(248,250,252,0.6);
}

:deep(.fc-daygrid-day-events) {
  min-height: 1.2em;
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .sandbox {
    padding: 20px 20px 40px;
  }
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .charts-row,
  .bottom-row {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 600px) {
  .metrics-grid {
    grid-template-columns: 1fr 1fr 1fr;
  }
  .community-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .content-tabs {
    flex-wrap: wrap;
  }
}
</style>
