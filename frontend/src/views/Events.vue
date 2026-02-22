<template>
  <div class="events-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">活动管理</h1>
        <p class="page-subtitle">策划、执行和复盘社区活动全流程</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        创建活动
      </el-button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px" @change="loadEvents">
        <el-option label="草稿" value="draft" />
        <el-option label="策划中" value="planning" />
        <el-option label="进行中" value="ongoing" />
        <el-option label="已完成" value="completed" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
      <el-select v-model="filterType" placeholder="类型筛选" clearable style="width: 140px" @change="loadEvents">
        <el-option label="线上" value="online" />
        <el-option label="线下" value="offline" />
        <el-option label="混合" value="hybrid" />
      </el-select>
    </div>

    <!-- Event List -->
    <div v-loading="loading" class="events-grid">
      <div v-if="!loading && events.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Flag /></el-icon>
        <p>暂无活动，点击右上角创建第一个活动</p>
      </div>
      <div
        v-for="event in events"
        :key="event.id"
        class="event-card"
        @click="$router.push(`/events/${event.id}`)"
      >
        <div class="event-card-header">
          <el-tag :type="typeTagMap[event.event_type] ?? 'info'" size="small">
            {{ typeLabel[event.event_type] ?? event.event_type }}
          </el-tag>
          <el-tag :type="statusTagMap[event.status] ?? 'info'" size="small">
            {{ statusLabel[event.status] ?? event.status }}
          </el-tag>
        </div>
        <h3 class="event-title">{{ event.title }}</h3>
        <div class="event-meta">
          <span v-if="event.planned_at">
            <el-icon><Calendar /></el-icon>
            {{ formatDate(event.planned_at) }}
          </span>
          <span v-if="event.location">
            <el-icon><Location /></el-icon>
            {{ event.location }}
          </span>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      class="pagination"
      @current-change="loadEvents"
    />

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建活动" width="500px" destroy-on-close>
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="活动名称" required>
          <el-input v-model="createForm.title" placeholder="请输入活动名称" />
        </el-form-item>
        <el-form-item label="活动类型">
          <el-select v-model="createForm.event_type" style="width: 100%">
            <el-option label="线下" value="offline" />
            <el-option label="线上" value="online" />
            <el-option label="混合" value="hybrid" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划时间">
          <el-date-picker v-model="createForm.planned_at" type="datetime" placeholder="选择时间" style="width: 100%" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="createForm.location" placeholder="活动地点（线下填写）" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="活动简介" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Flag, Plus, Calendar, Location } from '@element-plus/icons-vue'
import { listEvents, createEvent } from '../api/event'
import type { EventListItem } from '../api/event'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const events = ref<EventListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const filterStatus = ref<string>('')
const filterType = ref<string>('')
const showCreateDialog = ref(false)

const createForm = ref({
  title: '',
  event_type: 'offline',
  planned_at: null as string | null,
  location: '',
  description: '',
})

const statusLabel: Record<string, string> = {
  draft: '草稿',
  planning: '策划中',
  ongoing: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  draft: 'info',
  planning: 'warning',
  ongoing: 'primary',
  completed: 'success',
  cancelled: 'danger',
}

const typeLabel: Record<string, string> = {
  offline: '线下',
  online: '线上',
  hybrid: '混合',
}

const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  offline: '',
  online: 'success',
  hybrid: 'warning',
}

function formatDate(dt: string | null): string {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadEvents() {
  loading.value = true
  try {
    const data = await listEvents({
      status: filterStatus.value || undefined,
      event_type: filterType.value || undefined,
      page: currentPage.value,
      page_size: pageSize,
    })
    events.value = data.items
    total.value = data.total
  } catch {
    ElMessage.error('加载活动列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createForm.value = { title: '', event_type: 'offline', planned_at: null, location: '', description: '' }
  showCreateDialog.value = true
}

async function handleCreate() {
  if (!createForm.value.title.trim()) {
    ElMessage.warning('请输入活动名称')
    return
  }
  creating.value = true
  try {
    const event = await createEvent({
      title: createForm.value.title,
      event_type: createForm.value.event_type,
      planned_at: createForm.value.planned_at || null,
      location: createForm.value.location || null,
      description: createForm.value.description || null,
    })
    showCreateDialog.value = false
    ElMessage.success('活动已创建')
    router.push(`/events/${event.id}`)
  } catch {
    ElMessage.error('创建失败，请重试')
  } finally {
    creating.value = false
  }
}

onMounted(loadEvents)
</script>

<style scoped>
.events-page {
  padding: 24px 32px;
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
}

.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  min-height: 120px;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px;
  color: #94a3b8;
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
  color: #cbd5e1;
}

.event-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.event-card:hover {
  border-color: #0095ff;
  box-shadow: 0 4px 16px rgba(0, 149, 255, 0.12);
}

.event-card-header {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.event-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.event-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
}

.event-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
