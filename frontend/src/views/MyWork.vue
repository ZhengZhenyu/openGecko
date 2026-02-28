<template>
  <div class="my-work" v-loading="loading">
    <!-- 页面标题 -->
    <div class="page-title">
      <h2>我的工作</h2>
      <p class="subtitle">查看和管理我负责的所有任务</p>
    </div>

    <!-- 指标卡片 -->
    <div class="metric-cards">
      <div class="metric-card">
        <div class="metric-value">{{ allItems.length }}</div>
        <div class="metric-label">全部任务</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{{ totalPlanning }}</div>
        <div class="metric-label">计划中</div>
      </div>
      <div class="metric-card highlight-warning">
        <div class="metric-value">{{ totalInProgress }}</div>
        <div class="metric-label">进行中</div>
      </div>
      <div class="metric-card highlight-success">
        <div class="metric-value">{{ totalCompleted }}</div>
        <div class="metric-label">已完成</div>
      </div>
      <div class="metric-card" :class="totalOverdue > 0 ? 'highlight-danger' : ''">
        <div class="metric-value">{{ totalOverdue }}</div>
        <div class="metric-label">已逾期</div>
      </div>
    </div>

    <!-- 即将到期 / 逾期提醒 -->
    <div v-if="urgentItems.length > 0" class="section-card urgent-card">
      <div class="section-header">
        <div class="urgent-title">
          <el-icon class="urgent-icon"><Warning /></el-icon>
          <h3>待关注提醒</h3>
        </div>
        <span class="section-desc">{{ urgentItems.length }} 项需要关注，包含逾期或 72 小时内截止的未完成任务</span>
      </div>
      <div class="urgent-list">
        <div
          v-for="item in urgentItems"
          :key="`urgent-${item.type}-${item.id}`"
          class="urgent-item"
          :class="deadlineUrgency(item)"
          @click="goToDetail(item)"
        >
          <div class="urgent-item-left">
                <span class="count-badge" :class="item.type === 'content' ? 'content-badge' : item.type === 'meeting' ? 'meeting-badge' : item.type === 'checklist_item' ? 'checklist-item-badge' : item.type === 'campaign_task' ? 'campaign-task-badge' : 'event-task-badge'">
              {{ item.type === 'content' ? '内容' : item.type === 'meeting' ? '会议' : item.type === 'checklist_item' ? '清单项' : item.type === 'campaign_task' ? '关怀任务' : '活动任务' }}
            </span>
            <span class="urgent-item-title">{{ item.title }}</span>
          </div>
          <div class="urgent-item-right">
            <span class="deadline-badge" :class="deadlineBadgeClass(item)">
              {{ deadlineLabel(item) }}
            </span>
            <span class="deadline-date">{{ formatScheduledAt(item.scheduled_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="section-card filter-section">
      <el-radio-group v-model="filterStatus" @change="loadData">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="planning">计划中</el-radio-button>
        <el-radio-button value="in_progress">进行中</el-radio-button>
        <el-radio-button value="completed">已完成</el-radio-button>
      </el-radio-group>
      <el-radio-group v-model="filterType" style="margin-left: 16px;">
        <el-radio-button value="all">全部类型</el-radio-button>
        <el-radio-button value="content">内容</el-radio-button>
        <el-radio-button value="meeting">会议</el-radio-button>
        <el-radio-button value="event_task">活动任务</el-radio-button>
        <el-radio-button value="checklist_item">清单项</el-radio-button>
        <el-radio-button value="campaign_task">关怀任务</el-radio-button>
      </el-radio-group>
      <div class="filter-sort">
        <el-switch
          v-model="sortByDeadline"
          active-text="按截止日排序"
          style="--el-switch-on-color: #0095ff"
        />
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="section-card">
      <div class="section-header">
        <h3>任务列表</h3>
        <span class="section-desc">共 {{ filteredItems.length }} 项</span>
      </div>

      <div v-if="filteredItems.length === 0" class="empty-hint">暂无任务</div>

      <div v-else>
        <div
          v-for="item in filteredItems"
          :key="`${item.type}-${item.id}`"
          class="list-item clickable"
          @click="goToDetail(item)"
        >
          <div class="item-left">
            <span class="stat-dot" :class="statusDotClass(item.work_status)"></span>
            <div class="item-content">
              <div class="item-title-row">
                <span class="count-badge" :class="item.type === 'content' ? 'content-badge' : item.type === 'meeting' ? 'meeting-badge' : item.type === 'checklist_item' ? 'checklist-item-badge' : item.type === 'campaign_task' ? 'campaign-task-badge' : 'event-task-badge'">
                  {{ item.type === 'content' ? '内容' : item.type === 'meeting' ? '会议' : item.type === 'checklist_item' ? '清单项' : item.type === 'campaign_task' ? '关怀任务' : '活动任务' }}
                </span>
                <span class="item-title">{{ item.title }}</span>
              </div>
              <div class="item-meta">
                <span>{{ item.creator_name || '未知' }}</span>
                <span>{{ item.assignee_count }} 人参与</span>
                <span>{{ formatDate(item.updated_at) }}</span>
                <span v-if="item.scheduled_at" class="meta-deadline">
                  截止 {{ formatScheduledAt(item.scheduled_at) }}
                </span>
                <span
                  v-if="deadlineLabel(item)"
                  class="deadline-badge"
                  :class="deadlineBadgeClass(item)"
                >{{ deadlineLabel(item) }}</span>
              </div>
            </div>
          </div>
          <el-select
            v-if="item.type !== 'event_task' && item.type !== 'checklist_item'"
            v-model="item.work_status"
            @change="updateStatus(item)"
            @click.stop
            size="small"
            style="width: 110px; flex-shrink: 0;"
          >
            <el-option label="计划中" value="planning" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
          <span
            v-else
            class="event-task-status"
            @click.stop
          >{{ item.work_status === 'completed' ? '已完成' : item.work_status === 'in_progress' ? '进行中' : '计划中' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, Bell } from '@element-plus/icons-vue'
import axios from '../api'

const router = useRouter()

interface Item {
  id: number
  type: string
  title: string
  work_status: string
  creator_name?: string
  assignee_count: number
  updated_at: string
  scheduled_at?: string
  event_id?: number
}

const loading = ref(false)
const data = ref<any>(null)
const filterStatus = ref('all')
const filterType = ref('all')
const sortByDeadline = ref(false)

const allItems = computed(() => {
  if (!data.value) return []
  const eventTasks: Item[] = (data.value.event_tasks || []).map((t: any) => ({
    id: t.id,
    type: 'event_task',
    title: t.title,
    work_status: t.status === 'completed' ? 'completed' : t.status === 'in_progress' ? 'in_progress' : 'planning',
    creator_name: t.event_title || '',
    assignee_count: 0,
    updated_at: t.end_date || new Date().toISOString(),
    scheduled_at: t.end_date,
    event_id: t.event_id,
  }))
  const checklistItems: Item[] = (data.value.checklist_items || []).map((c: any) => ({
    id: c.id,
    type: 'checklist_item',
    title: c.title,
    work_status: c.status === 'done' ? 'completed' : 'planning',
    creator_name: c.event_title || '',
    assignee_count: 0,
    updated_at: c.due_date || new Date().toISOString(),
    scheduled_at: c.due_date,
    event_id: c.event_id,
  }))
  const campaignTaskItems: Item[] = (data.value.campaign_tasks || []).map((t: any) => ({
    id: t.id,
    type: 'campaign_task',
    title: t.title,
    work_status: t.status === 'completed' ? 'completed' : t.status === 'in_progress' ? 'in_progress' : 'planning',
    creator_name: t.campaign_name || '',
    assignee_count: 0,
    updated_at: t.deadline || new Date().toISOString(),
    scheduled_at: t.deadline,
  }))
  return [...data.value.contents, ...data.value.meetings, ...eventTasks, ...checklistItems, ...campaignTaskItems]
})

const filteredItems = computed(() => {
  let items = allItems.value
  if (filterStatus.value !== 'all') items = items.filter((i: Item) => i.work_status === filterStatus.value)
  if (filterType.value !== 'all') items = items.filter((i: Item) => i.type === filterType.value)
  if (sortByDeadline.value) {
    items = [...items].sort((a: Item, b: Item) => {
      if (!a.scheduled_at && !b.scheduled_at) return 0
      if (!a.scheduled_at) return 1
      if (!b.scheduled_at) return -1
      return new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
    })
  }
  return items
})

// 即将到期 / 逾期的任务（未完成且截止日期在 72 小时内或已过期）
const urgentItems = computed(() => {
  const now = Date.now()
  const h72 = 72 * 60 * 60 * 1000
  return allItems.value.filter((i: Item) => {
    if (i.work_status === 'completed') return false
    if (!i.scheduled_at) return false
    const diff = new Date(i.scheduled_at).getTime() - now
    return diff < h72
  }).sort((a: Item, b: Item) => {
    return new Date(a.scheduled_at!).getTime() - new Date(b.scheduled_at!).getTime()
  })
})

const totalPlanning = computed(() => {
  if (!data.value) return 0
  return data.value.content_stats.planning
    + data.value.meeting_stats.planning
    + (data.value.event_task_stats?.planning ?? 0)
    + (data.value.checklist_item_stats?.planning ?? 0)
    + (data.value.care_contact_stats?.planning ?? 0)
})
const totalInProgress = computed(() => {
  if (!data.value) return 0
  return data.value.content_stats.in_progress
    + data.value.meeting_stats.in_progress
    + (data.value.event_task_stats?.in_progress ?? 0)
    + (data.value.checklist_item_stats?.in_progress ?? 0)
    + (data.value.care_contact_stats?.in_progress ?? 0)
})
const totalCompleted = computed(() => {
  if (!data.value) return 0
  return data.value.content_stats.completed
    + data.value.meeting_stats.completed
    + (data.value.event_task_stats?.completed ?? 0)
    + (data.value.checklist_item_stats?.completed ?? 0)
    + (data.value.care_contact_stats?.completed ?? 0)
})
const totalOverdue = computed(() => {
  const now = Date.now()
  return allItems.value.filter((i: Item) =>
    i.work_status !== 'completed' && i.scheduled_at && new Date(i.scheduled_at).getTime() < now
  ).length
})

const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

function formatScheduledAt(dateStr?: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function deadlineUrgency(item: Item): 'overdue' | 'today' | 'tomorrow' | 'soon' | null {
  if (!item.scheduled_at || item.work_status === 'completed') return null
  const now = Date.now()
  const ts = new Date(item.scheduled_at).getTime()
  const diff = ts - now
  if (diff < 0) return 'overdue'
  if (diff < 24 * 3600 * 1000) return 'today'
  if (diff < 48 * 3600 * 1000) return 'tomorrow'
  if (diff < 72 * 3600 * 1000) return 'soon'
  return null
}

function deadlineLabel(item: Item): string {
  const urgency = deadlineUrgency(item)
  if (!urgency) return ''
  const map: Record<string, string> = { overdue: '已逾期', today: '今日截止', tomorrow: '明日截止', soon: '即将截止' }
  return map[urgency]
}

function deadlineBadgeClass(item: Item): string {
  const urgency = deadlineUrgency(item)
  if (!urgency) return ''
  const map: Record<string, string> = {
    overdue: 'deadline-overdue',
    today: 'deadline-today',
    tomorrow: 'deadline-tomorrow',
    soon: 'deadline-soon',
  }
  return map[urgency]
}

function statusDotClass(status: string) {
  const map: Record<string, string> = { planning: 'planning', in_progress: 'in-progress', completed: 'completed' }
  return map[status] || 'planning'
}

const loadData = async () => {
  loading.value = true
  try {
    const { data: res } = await axios.get('/users/me/dashboard')
    data.value = res
  } catch (error: any) {
    ElMessage.error('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const updateStatus = async (item: Item) => {
  const url = `/users/me/${item.type === 'content' ? 'contents' : 'meetings'}/${item.id}/work-status`
  try {
    await axios.patch(url, { work_status: item.work_status })
    ElMessage.success('状态已更新')
    loadData()
  } catch (error: any) {
    ElMessage.error('更新失败: ' + (error.response?.data?.detail || error.message))
    loadData()
  }
}

const goToDetail = (item: Item) => {
  if (item.type === 'content') {
    router.push(`/contents/${item.id}/edit`)
  } else if (item.type === 'meeting') {
    router.push(`/meetings/${item.id}`)
  } else if (item.type === 'event_task' || item.type === 'checklist_item') {
    router.push(`/events/${item.event_id}`)
  } else if (item.type === 'campaign_task') {
    router.push('/campaigns')
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.my-work {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --orange: #f59e0b;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page Title */
.page-title {
  margin-bottom: 32px;
  padding: 0 4px;
}

.page-title h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-title .subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 15px;
}

/* Metric Cards */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.metric-card {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}

.metric-card:hover {
  box-shadow: var(--shadow-hover);
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.metric-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.metric-card.highlight-warning .metric-value {
  color: var(--orange);
}

.metric-card.highlight-success .metric-value {
  color: var(--green);
}

/* Section Card */
.section-card {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-desc {
  font-size: 14px;
  color: var(--text-muted);
}

/* Filter Section */
.filter-section {
  display: flex;
  align-items: center;
  padding: 20px 28px;
}

/* List Item */
.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

.list-item:last-child {
  border-bottom: none;
}

.list-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.list-item.clickable:hover {
  background: var(--bg-hover);
  margin: 0 -28px;
  padding: 16px 28px;
  border-radius: 8px;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  flex: 1;
}

/* Status Dot */
.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-dot.planning {
  background: var(--text-muted);
}

.stat-dot.in-progress {
  background: var(--orange);
}

.stat-dot.completed {
  background: var(--green);
}

.item-content {
  min-width: 0;
  flex: 1;
}

.item-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.item-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  gap: 18px;
  font-size: 13px;
  color: var(--text-muted);
}

/* Badges */
.count-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
}

.content-badge {
  background: #eff6ff;
  color: #1d4ed8;
}

.meeting-badge {
  background: #f0fdf4;
  color: #15803d;
}

.event-task-badge {
  background: #fffbeb;
  color: #b45309;
}

.checklist-item-badge {
  background: #f5f3ff;
  color: #6d28d9;
}

.campaign-task-badge {
  background: #f0fdf4;
  color: #15803d;
}

.event-task-status {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #64748b;
  flex-shrink: 0;
  white-space: nowrap;
}

/* Empty */
.empty-hint {
  color: var(--text-muted);
  text-align: center;
  padding: 48px 0;
  font-size: 14px;
}

/* Deadline badges */
.deadline-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}
.deadline-overdue  { background: #fef2f2; color: #dc2626; }
.deadline-today    { background: #fff7ed; color: #c2410c; }
.deadline-tomorrow { background: #fffbeb; color: #b45309; }
.deadline-soon     { background: #eff6ff; color: #1d4ed8; }

.meta-deadline {
  color: var(--text-muted);
}

/* Highlight danger metric */
.metric-card.highlight-danger .metric-value {
  color: #ef4444;
}

/* Filter bar sort toggle */
.filter-sort {
  margin-left: auto;
}

/* Urgent card */
.urgent-card {
  border-left: 4px solid #ef4444;
}
.urgent-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.urgent-title h3 {
  color: #dc2626;
}
.urgent-icon {
  color: #ef4444;
  font-size: 18px;
}
.urgent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.urgent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.urgent-item:hover {
  background: #f8fafc;
}
.urgent-item.overdue  { background: #fff5f5; }
.urgent-item.today    { background: #fff7f0; }
.urgent-item.tomorrow { background: #fffef0; }
.urgent-item.soon     { background: #f0f7ff; }
.urgent-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}
.urgent-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.urgent-item-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.deadline-date {
  font-size: 13px;
  color: var(--text-muted);
}

/* Responsive */
@media (max-width: 1200px) {
  .my-work { padding: 28px 24px; }
  .metric-cards { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 734px) {
  .my-work { padding: 20px 16px; }
  .metric-cards { grid-template-columns: repeat(2, 1fr); }
  .filter-section { flex-wrap: wrap; gap: 12px; }
  .page-title h2 { font-size: 22px; }
}
</style>
