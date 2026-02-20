<template>
  <div class="workload-overview" v-loading="loading">
    <!-- 页面标题 -->
    <div class="page-title">
      <h2>工作量总览</h2>
      <p class="subtitle">查看所有成员的任务分配和完成情况</p>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="metric-cards">
      <div class="metric-card">
        <div class="metric-value">{{ users.length }}</div>
        <div class="metric-label">活跃成员</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{{ totalItems }}</div>
        <div class="metric-label">总任务数</div>
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

    <!-- 排行榜 -->
    <div class="leaderboard-section">
      <div class="section-header">
        <h3>成员工作量排行</h3>
        <span class="section-desc">按总任务数排序</span>
      </div>
      <div class="leaderboard">
        <div
          v-for="(user, index) in sortedUsers"
          :key="user.user_id"
          class="leaderboard-item"
        >
          <div class="rank-badge" :class="rankClass(index)">{{ index + 1 }}</div>
          <div class="user-info">
            <div class="user-avatar">{{ (user.full_name || user.username).charAt(0).toUpperCase() }}</div>
            <div class="user-detail">
              <span class="user-name">{{ user.full_name || user.username }}</span>
              <span class="user-username">@{{ user.username }}</span>
            </div>
          </div>
          <div class="task-bar-wrapper">
            <div class="task-bar">
              <div
                class="bar-segment planning"
                :style="{ width: barWidth(user, 'planning') }"
                :title="`计划中: ${contentPlanning(user) + meetingPlanning(user)}`"
              />
              <div
                class="bar-segment in-progress"
                :style="{ width: barWidth(user, 'in_progress') }"
                :title="`进行中: ${contentInProgress(user) + meetingInProgress(user)}`"
              />
              <div
                class="bar-segment completed"
                :style="{ width: barWidth(user, 'completed') }"
                :title="`已完成: ${contentCompleted(user) + meetingCompleted(user)}`"
              />
            </div>
          </div>
          <div class="task-counts">
            <el-tooltip content="内容任务" placement="top">
              <span class="count-badge content-badge">
                <el-icon :size="12"><Document /></el-icon>
                {{ contentTotal(user) }}
              </span>
            </el-tooltip>
            <el-tooltip content="会议任务" placement="top">
              <span class="count-badge meeting-badge">
                <el-icon :size="12"><Calendar /></el-icon>
                {{ meetingTotal(user) }}
              </span>
            </el-tooltip>
            <span class="total-count">{{ user.total }}</span>
          </div>
        </div>
        <div v-if="sortedUsers.length === 0 && !loading" class="empty-state">
          暂无数据
        </div>
      </div>
    </div>

    <!-- 详细数据展开 -->
    <div class="detail-section">
      <div class="section-header">
        <h3>详细工作量</h3>
      </div>
      <div class="detail-grid">
        <div
          v-for="user in sortedUsers"
          :key="'detail-' + user.user_id"
          class="detail-card"
        >
          <div class="detail-card-header">
            <div class="user-avatar small">{{ (user.full_name || user.username).charAt(0).toUpperCase() }}</div>
            <div>
              <div class="user-name">{{ user.full_name || user.username }}</div>
              <div class="user-username">@{{ user.username }}</div>
            </div>
            <div class="total-badge">{{ user.total }} 任务</div>
          </div>
          <div class="detail-card-body">
            <div class="stat-group">
              <div class="stat-group-title">
                <el-icon :size="14"><Document /></el-icon> 内容任务
              </div>
              <div class="stat-row">
                <span class="stat-dot planning" />
                <span class="stat-label">计划中</span>
                <span class="stat-value">{{ user.content_stats.planning }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-dot in-progress" />
                <span class="stat-label">进行中</span>
                <span class="stat-value">{{ user.content_stats.in_progress }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-dot completed" />
                <span class="stat-label">已完成</span>
                <span class="stat-value">{{ user.content_stats.completed }}</span>
              </div>
            </div>
            <div class="stat-group">
              <div class="stat-group-title">
                <el-icon :size="14"><Calendar /></el-icon> 会议任务
              </div>
              <div class="stat-row">
                <span class="stat-dot planning" />
                <span class="stat-label">计划中</span>
                <span class="stat-value">{{ user.meeting_stats.planning }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-dot in-progress" />
                <span class="stat-label">进行中</span>
                <span class="stat-value">{{ user.meeting_stats.in_progress }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-dot completed" />
                <span class="stat-label">已完成</span>
                <span class="stat-value">{{ user.meeting_stats.completed }}</span>
              </div>
            </div>
            <div class="stat-group">
              <div class="stat-group-title">内容类型分布</div>
              <div class="type-tags">
                <el-tag v-if="user.content_by_type.contribution > 0" size="small" type="primary">
                  贡献 {{ user.content_by_type.contribution }}
                </el-tag>
                <el-tag v-if="user.content_by_type.release_note > 0" size="small" type="success">
                  发行说明 {{ user.content_by_type.release_note }}
                </el-tag>
                <el-tag v-if="user.content_by_type.event_summary > 0" size="small" type="warning">
                  活动总结 {{ user.content_by_type.event_summary }}
                </el-tag>
                <span v-if="contentTotal(user) === 0" class="no-data">暂无内容</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend">
      <span class="legend-item"><span class="legend-dot planning" /> 计划中</span>
      <span class="legend-item"><span class="legend-dot in-progress" /> 进行中</span>
      <span class="legend-item"><span class="legend-dot completed" /> 已完成</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Calendar } from '@element-plus/icons-vue'
import apiClient from '../api'

interface WorkStatusStats {
  planning: number
  in_progress: number
  completed: number
}

interface ContentByTypeStats {
  contribution: number
  release_note: number
  event_summary: number
}

interface UserWorkloadItem {
  user_id: number
  username: string
  full_name: string | null
  content_stats: WorkStatusStats
  meeting_stats: WorkStatusStats
  content_by_type: ContentByTypeStats
  total: number
}

const users = ref<UserWorkloadItem[]>([])
const loading = ref(false)

const sortedUsers = computed(() =>
  [...users.value].sort((a, b) => b.total - a.total)
)

const totalItems = computed(() => users.value.reduce((sum, u) => sum + u.total, 0))
const totalInProgress = computed(() =>
  users.value.reduce((sum, u) => sum + u.content_stats.in_progress + u.meeting_stats.in_progress, 0)
)
const totalCompleted = computed(() =>
  users.value.reduce((sum, u) => sum + u.content_stats.completed + u.meeting_stats.completed, 0)
)

const maxTotal = computed(() => Math.max(...users.value.map(u => u.total), 1))

// Helper functions
const contentPlanning = (u: UserWorkloadItem) => u.content_stats.planning
const contentInProgress = (u: UserWorkloadItem) => u.content_stats.in_progress
const contentCompleted = (u: UserWorkloadItem) => u.content_stats.completed
const contentTotal = (u: UserWorkloadItem) => u.content_stats.planning + u.content_stats.in_progress + u.content_stats.completed
const meetingPlanning = (u: UserWorkloadItem) => u.meeting_stats.planning
const meetingInProgress = (u: UserWorkloadItem) => u.meeting_stats.in_progress
const meetingCompleted = (u: UserWorkloadItem) => u.meeting_stats.completed
const meetingTotal = (u: UserWorkloadItem) => u.meeting_stats.planning + u.meeting_stats.in_progress + u.meeting_stats.completed

function barWidth(user: UserWorkloadItem, status: string) {
  const total = user.total
  if (total === 0) return '0%'
  let count = 0
  if (status === 'planning') count = contentPlanning(user) + meetingPlanning(user)
  else if (status === 'in_progress') count = contentInProgress(user) + meetingInProgress(user)
  else if (status === 'completed') count = contentCompleted(user) + meetingCompleted(user)
  // Scale relative to maxTotal so the top user fills the bar
  return `${(count / maxTotal.value) * 100}%`
}

function rankClass(index: number) {
  if (index === 0) return 'gold'
  if (index === 1) return 'silver'
  if (index === 2) return 'bronze'
  return ''
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await apiClient.get('/users/me/workload-overview')
    users.value = data.users
  } catch (error: any) {
    ElMessage.error('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.workload-overview {
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

  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 40px 60px;
  position: relative;
}

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
.metric-card.highlight-warning .metric-value { color: #f59e0b; }
.metric-card.highlight-success .metric-value { color: #22c55e; }

/* Section */
.leaderboard-section, .detail-section {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}
.leaderboard-section:hover, .detail-section:hover {
  box-shadow: var(--shadow-hover);
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

/* Leaderboard */
.leaderboard-item {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s ease;
}
.leaderboard-item:last-child {
  border-bottom: none;
}
.leaderboard-item:hover {
  background: #f8fafc;
  margin: 0 -28px;
  padding: 16px 28px;
  border-radius: 8px;
}

.rank-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  background: #f8fafc;
  flex-shrink: 0;
}
.rank-badge.gold { background: #fffbeb; color: #f59e0b; }
.rank-badge.silver { background: #f8fafc; color: #94a3b8; }
.rank-badge.bronze { background: #fef3c7; color: #d97706; }

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
  flex-shrink: 0;
}
.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #93c5fd, #a5b4fc);
  color: #1e40af;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  flex-shrink: 0;
}
.user-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.user-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.user-username {
  font-size: 12px;
  color: var(--text-muted);
}

.task-bar-wrapper {
  flex: 1;
  min-width: 0;
}
.task-bar {
  display: flex;
  height: 22px;
  border-radius: 6px;
  overflow: hidden;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
}
.bar-segment {
  height: 100%;
  transition: width 0.4s ease;
  min-width: 0;
}
.bar-segment.planning { background: #94a3b8; }
.bar-segment.in-progress { background: #f59e0b; }
.bar-segment.completed { background: #22c55e; }

.task-counts {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  min-width: 160px;
  justify-content: flex-end;
}
.count-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
}
.content-badge { background: #eff6ff; color: #1d4ed8; }
.meeting-badge { background: #f0fdf4; color: #15803d; }
.total-count {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 40px;
  text-align: right;
}

/* Detail Grid */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}
.detail-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: #ffffff;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}
.detail-card:hover {
  box-shadow: var(--shadow-hover);
}
.detail-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}
.detail-card-header .user-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.detail-card-header .user-username { font-size: 12px; color: var(--text-muted); }
.total-badge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 500;
  color: #1d4ed8;
  background: #eff6ff;
  padding: 4px 12px;
  border-radius: 6px;
}
.detail-card-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.stat-group-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.stat-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}
.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stat-dot.planning { background: #94a3b8; }
.stat-dot.in-progress { background: #f59e0b; }
.stat-dot.completed { background: #22c55e; }
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  flex: 1;
}
.stat-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.type-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.no-data {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

/* Legend */
.legend {
  display: flex;
  gap: 24px;
  justify-content: center;
  padding: 18px 0;
  color: var(--text-muted);
  font-size: 13px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 4px;
}
.legend-dot.planning { background: #94a3b8; }
.legend-dot.in-progress { background: #f59e0b; }
.legend-dot.completed { background: #22c55e; }

.empty-state {
  text-align: center;
  padding: 48px;
  color: var(--text-muted);
  font-size: 14px;
}
</style>
