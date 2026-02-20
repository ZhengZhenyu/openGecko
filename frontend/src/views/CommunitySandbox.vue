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
          <el-button size="small" @click="$router.push('/contents/new')">
            <el-icon><Plus /></el-icon> 新建内容
          </el-button>
          <el-button
            v-if="isCurrentCommunityAdmin"
            size="small"
            @click="$router.push(`/community-settings/${communityStore.currentCommunityId}`)"
          >
            <el-icon><Setting /></el-icon> 社区设置
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
        <!-- 第一层：8 指标卡片 (2行x4列) -->
        <div class="metrics-grid">
          <div class="metric-card" @click="$router.push('/contents')">
            <div class="metric-icon-wrap content-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.total_contents }}</div>
              <div class="metric-label">内容总数</div>
            </div>
          </div>
          <div class="metric-card highlight-green" @click="$router.push('/contents?status=published')">
            <div class="metric-icon-wrap publish-icon">
              <el-icon><Promotion /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.published_contents }}</div>
              <div class="metric-label">已发布</div>
            </div>
          </div>
          <div class="metric-card highlight-orange" @click="$router.push('/contents?status=reviewing')">
            <div class="metric-icon-wrap review-icon">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.reviewing_contents }}</div>
              <div class="metric-label">待审核</div>
            </div>
          </div>
          <div class="metric-card" @click="$router.push('/contents?status=draft')">
            <div class="metric-icon-wrap draft-icon">
              <el-icon><EditPen /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.draft_contents }}</div>
              <div class="metric-label">草稿</div>
            </div>
          </div>
          <div class="metric-card" @click="$router.push('/governance')">
            <div class="metric-icon-wrap gov-icon">
              <el-icon><Stamp /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.total_committees }}</div>
              <div class="metric-label">委员会</div>
            </div>
          </div>
          <div class="metric-card" @click="$router.push('/communities')">
            <div class="metric-icon-wrap member-icon">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ dashboardData.metrics.total_members }}</div>
              <div class="metric-label">成员数</div>
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

        <!-- 第二层：趋势图 + 渠道统计 -->
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

        <!-- 第三层：社区事件日历（全宽） -->
        <div class="section-card calendar-card">
          <div class="card-header">
            <h3>社区事件日历</h3>
            <div class="calendar-legend">
              <span class="legend-dot meeting-dot"></span><span class="legend-text">会议</span>
              <span class="legend-dot publish-dot"></span><span class="legend-text">内容发布</span>
              <span class="legend-dot member-dot"></span><span class="legend-text">成员活动</span>
            </div>
          </div>
          <FullCalendar ref="calendarRef" :options="calendarOptions" class="community-calendar" />
        </div>

        <!-- 第四层：最近内容 + 即将事件 -->
        <div class="bottom-row">
          <div class="section-card">
            <div class="card-header">
              <h3>最近内容</h3>
              <router-link to="/contents" class="view-all">查看全部 →</router-link>
            </div>
            <div v-if="dashboardData.recent_contents.length === 0" class="empty-hint">暂无内容</div>
            <div v-else class="content-list">
              <div
                v-for="item in dashboardData.recent_contents"
                :key="item.id"
                class="content-list-item"
                @click="$router.push(`/contents/${item.id}/edit`)"
              >
                <div class="content-title">{{ item.title }}</div>
                <div class="content-meta">
                  <span class="status-badge" :class="statusClass(item.status)">
                    {{ statusLabel(item.status) }}
                  </span>
                  <span class="meta-text">{{ item.owner_name }}</span>
                  <span class="meta-text">{{ formatDate(item.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="section-card">
            <div class="card-header">
              <h3>即将到来的会议</h3>
              <router-link to="/meetings" class="view-all">查看全部 →</router-link>
            </div>
            <div v-if="dashboardData.upcoming_meetings.length === 0" class="empty-hint">
              近期无会议安排
            </div>
            <div v-else class="meeting-list">
              <div
                v-for="m in dashboardData.upcoming_meetings"
                :key="m.id"
                class="meeting-item"
                @click="$router.push(`/meetings/${m.id}`)"
              >
                <div class="meeting-date-col">
                  <div class="meeting-day">{{ formatDay(m.scheduled_at) }}</div>
                  <div class="meeting-month">{{ formatMonth(m.scheduled_at) }}</div>
                </div>
                <div class="meeting-info">
                  <div class="meeting-title">{{ m.title }}</div>
                  <div class="meeting-committee">{{ m.committee_name }}</div>
                </div>
                <div class="meeting-time">{{ formatTime(m.scheduled_at) }}</div>
              </div>
            </div>
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
import type { CalendarOptions } from '@fullcalendar/core'
import {
  Document, Promotion, Clock, EditPen, Stamp, UserFilled,
  Calendar, Connection, Plus, Setting,
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'
import { getCommunityDashboard, type CommunityDashboardResponse } from '../api/communityDashboard'

// 按需注册 ECharts 组件（Tree Shaking）
use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent])

const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const loading = ref(false)
const dashboardData = ref<CommunityDashboardResponse | null>(null)
const calendarRef = ref()

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
  return (m.total_contents || 0) === 0 && (m.total_members || 0) <= 1
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

onMounted(() => {
  if (communityStore.currentCommunityId) loadDashboard()
})

watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) loadDashboard()
    else dashboardData.value = null
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
  height: 400,
  events: (dashboardData.value?.calendar_events ?? []).map((e) => ({
    id: e.id,
    title: e.title,
    date: e.date,
    color: e.color,
    extendedProps: { type: e.type, resource_id: e.resource_id, resource_type: e.resource_type },
  })),
  eventClick: (info) => {
    const { type, resource_id } = info.event.extendedProps
    if (type === 'meeting') router.push(`/meetings/${resource_id}`)
    else if (type === 'publish') router.push(`/contents/${resource_id}/edit`)
  },
  dayMaxEvents: 3,
}))

// ===== 工具函数 =====

function statusLabel(s: string) {
  const m: Record<string, string> = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布' }
  return m[s] || s
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
.community-logo img {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  object-fit: cover;
  border: 1px solid var(--border);
}
.community-logo-placeholder {
  width: 56px;
  height: 56px;
  border-radius: 12px;
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
.onboarding-right {}

/* ===== 骨架屏 ===== */
.skeleton-wrap {
  padding: 24px 0;
}

/* ===== 8 指标卡片网格 ===== */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
  gap: 14px;
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.meeting-dot { background: #0095ff; }
.publish-dot  { background: #10b981; }
.member-dot   { background: #f59e0b; }
.legend-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin-right: 4px;
}

/* ===== 底部两栏 ===== */
.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* ===== 最近内容列表 ===== */
.content-list-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}
.content-list-item:last-child { border-bottom: none; }
.content-list-item:hover { color: var(--blue); }
.content-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.content-list-item:hover .content-title { color: var(--blue); }
.content-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.meta-text {
  font-size: 12px;
  color: var(--text-muted);
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

/* ===== 会议列表 ===== */
.meeting-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}
.meeting-item:last-child { border-bottom: none; }
.meeting-item:hover .meeting-title { color: var(--blue); }
.meeting-date-col {
  text-align: center;
  width: 36px;
  flex-shrink: 0;
}
.meeting-day {
  font-size: 20px;
  font-weight: 700;
  color: var(--blue);
  line-height: 1;
}
.meeting-month {
  font-size: 11px;
  color: var(--text-muted);
}
.meeting-info {
  flex: 1;
  min-width: 0;
}
.meeting-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meeting-committee {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
.meeting-time {
  font-size: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

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
:deep(.fc-toolbar-title) {
  font-size: 15px !important;
  font-weight: 600;
  color: var(--text-primary);
}
:deep(.fc-button) {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-secondary) !important;
  font-size: 13px !important;
  padding: 4px 10px !important;
  box-shadow: none !important;
}
:deep(.fc-button:hover) {
  background: #f8fafc !important;
  color: var(--blue) !important;
  border-color: var(--blue) !important;
}
:deep(.fc-button-active) {
  background: #eff6ff !important;
  color: var(--blue) !important;
  border-color: var(--blue) !important;
}
:deep(.fc-day-today) {
  background: #f0f9ff !important;
}
:deep(.fc-daygrid-day-number) {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 4px 6px;
}
:deep(.fc-col-header-cell-cushion) {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
}
:deep(.fc-event) {
  font-size: 11px;
  border-radius: 4px;
  padding: 1px 4px;
  border: none;
  cursor: pointer;
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
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row,
  .bottom-row {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 600px) {
  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }
  .community-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
