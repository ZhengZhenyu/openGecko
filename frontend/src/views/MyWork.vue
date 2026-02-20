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
      </el-radio-group>
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
                <span class="count-badge" :class="item.type === 'content' ? 'content-badge' : 'meeting-badge'">
                  {{ item.type === 'content' ? '内容' : '会议' }}
                </span>
                <span class="item-title">{{ item.title }}</span>
              </div>
              <div class="item-meta">
                <span>{{ item.creator_name || '未知' }}</span>
                <span>{{ item.assignee_count }} 人参与</span>
                <span>{{ formatDate(item.updated_at) }}</span>
              </div>
            </div>
          </div>
          <el-select
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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
}

const loading = ref(false)
const data = ref<any>(null)
const filterStatus = ref('all')
const filterType = ref('all')

const allItems = computed(() => {
  if (!data.value) return []
  return [...data.value.contents, ...data.value.meetings]
})

const filteredItems = computed(() => {
  let items = allItems.value
  if (filterStatus.value !== 'all') items = items.filter((i: Item) => i.work_status === filterStatus.value)
  if (filterType.value !== 'all') items = items.filter((i: Item) => i.type === filterType.value)
  return items
})

const totalPlanning = computed(() =>
  data.value ? (data.value.content_stats.planning + data.value.meeting_stats.planning) : 0
)
const totalInProgress = computed(() =>
  data.value ? (data.value.content_stats.in_progress + data.value.meeting_stats.in_progress) : 0
)
const totalCompleted = computed(() =>
  data.value ? (data.value.content_stats.completed + data.value.meeting_stats.completed) : 0
)

const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

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

/* Empty */
.empty-hint {
  color: var(--text-muted);
  text-align: center;
  padding: 48px 0;
  font-size: 14px;
}

/* Element Plus overrides */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

:deep(.el-button--default:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

:deep(.el-button--text) {
  color: var(--blue);
}

:deep(.el-button--text:hover) {
  background: #f0f9ff;
}
</style>
