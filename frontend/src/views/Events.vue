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
       <el-input
         v-model="filterKeyword"
         placeholder="搜索活动名称"
         clearable
         style="width: 200px"
         @input="debouncedLoadEvents"
         @clear="debouncedLoadEvents"
       >
         <template #prefix>
           <el-icon><Search /></el-icon>
         </template>
       </el-input>
       <el-select v-model="filterCommunity" placeholder="社区筛选" clearable style="width: 160px" @change="loadEvents">
         <el-option
           v-for="c in communities"
           :key="c.id"
           :label="c.name"
           :value="c.id"
         />
       </el-select>
       <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px" @change="loadEvents">
         <el-option label="策划中" value="planning" />
         <el-option label="进行中" value="ongoing" />
         <el-option label="已完成" value="completed" />
       </el-select>
       <el-select v-model="filterType" placeholder="类型筛选" clearable style="width: 140px" @change="loadEvents">
         <el-option label="线上" value="online" />
         <el-option label="线下" value="offline" />
         <el-option label="混合" value="hybrid" />
       </el-select>
       <el-radio-group v-model="viewMode" class="view-toggle">
         <el-radio-button value="list">
           <el-icon><List /></el-icon>
           列表
         </el-radio-button>
         <el-radio-button value="calendar">
           <el-icon><Calendar /></el-icon>
           日历
         </el-radio-button>
       </el-radio-group>
     </div>

      <!-- Event List -->
      <div v-if="viewMode === 'list'" v-loading="loading" class="events-table-container">
        <div v-if="!loading && events.length === 0" class="empty-state">
          <el-icon class="empty-icon"><Flag /></el-icon>
          <p>暂无活动，点击右上角创建第一个活动</p>
        </div>
        <el-table v-else :data="events" style="width: 100%" @row-click="(row: EventListItem) => $router.push('/events/' + row.id)">
          <el-table-column prop="title" label="活动名称" min-width="200" />
          <el-table-column prop="event_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="typeTagMap[row.event_type] ?? 'info'" size="small">
                {{ typeLabel[row.event_type] ?? row.event_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusTagMap[row.status] ?? 'info'" size="small">
                {{ statusLabel[row.status] ?? row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="planned_at" label="计划时间" width="180">
            <template #default="{ row }">
              <span v-if="row.planned_at">{{ formatDate(row.planned_at) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="location" label="地点" min-width="150" />
          <el-table-column prop="community_id" label="社区" width="140">
            <template #default="{ row }">
              <el-tooltip
                v-if="row.community_id"
                :content="getCommunityName(row.community_id) || `社区 #${row.community_id}`"
                placement="top"
                :show-after="300"
              >
                <el-tag type="primary" size="small" effect="plain" class="community-tag">
                  {{ getCommunityName(row.community_id) || `#${row.community_id}` }}
                </el-tag>
              </el-tooltip>
              <span v-else class="no-community">—</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <div class="action-buttons" @click.stop>
                <el-popconfirm title="确定永久删除此活动？" @confirm="handleDeleteEvent(row)">
                  <template #reference>
                    <el-button size="small" link type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>
     </div>

    <!-- Calendar View -->
    <div v-if="viewMode === 'calendar'" class="calendar-container">
      <FullCalendar ref="calendarRef" :options="calendarOptions" class="events-calendar" />
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
        <el-form-item label="关联社区">
          <el-select v-model="createForm.community_id" placeholder="可选，关联到某社区" clearable style="width: 100%">
            <el-option
              v-for="c in communities"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Flag, Plus, Calendar, Location, Search, List } from '@element-plus/icons-vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { CalendarOptions, EventClickArg, EventDropArg } from '@fullcalendar/core'
import { listEvents, createEvent, updateEvent, deleteEvent } from '../api/event'
import type { EventListItem } from '../api/event'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const communities = computed(() => authStore.communities)

const loading = ref(false)
const creating = ref(false)
const events = ref<EventListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const filterStatus = ref<string>('')
const filterType = ref<string>('')
const filterCommunity = ref<number | null>(null)
const filterKeyword = ref<string>('')
const showCreateDialog = ref(false)
const viewMode = ref<'list' | 'calendar'>('list')
const calendarRef = ref()

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const createForm = ref({
  title: '',
  event_type: 'offline',
  community_id: null as number | null,
  planned_at: null as string | null,
  location: '',
  description: '',
})

const statusLabel: Record<string, string> = {
  planning: '策划中',
  ongoing: '进行中',
  completed: '已完成',
}

const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  planning: 'warning',
  ongoing: 'primary',
  completed: 'success',
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

function getCommunityName(communityId: number | null): string {
  if (!communityId) return ''
  const community = communities.value.find(c => c.id === communityId)
  return community?.name || ''
}

function debouncedLoadEvents() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    loadEvents()
  }, 500)
}

const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-cn',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  buttonText: { today: '今天' },
  height: 500,
  events: events.value.map(e => ({
    id: String(e.id),
    title: e.title,
    date: e.planned_at ? new Date(e.planned_at) : undefined,
    color: statusTagMap[e.status] === 'primary' ? '#0095ff' : 
            statusTagMap[e.status] === 'success' ? '#10b981' :
            statusTagMap[e.status] === 'warning' ? '#f59e0b' :
            statusTagMap[e.status] === 'danger' ? '#ef4444' : '#94a3b8',
    extendedProps: { type: 'event', resource_id: e.id },
  })),
  editable: true,
  eventClick: (info: EventClickArg) => {
    router.push(`/events/${info.event.id}`)
  },
  eventDrop: async (info: EventDropArg) => {
    const id = Number(info.event.id)
    const newStart = info.event.start
    if (!newStart) { info.revert(); return }
    // 保留原有时间部分，只替换日期
    const original = events.value.find(e => e.id === id)
    let newDateStr: string
    if (original?.planned_at) {
      const orig = new Date(original.planned_at)
      const hours = orig.getHours().toString().padStart(2, '0')
      const mins  = orig.getMinutes().toString().padStart(2, '0')
      const secs  = orig.getSeconds().toString().padStart(2, '0')
      const pad = (n: number) => String(n).padStart(2, '0')
      newDateStr = `${newStart.getFullYear()}-${pad(newStart.getMonth()+1)}-${pad(newStart.getDate())}T${hours}:${mins}:${secs}`
    } else {
      const pad = (n: number) => String(n).padStart(2, '0')
      newDateStr = `${newStart.getFullYear()}-${pad(newStart.getMonth()+1)}-${pad(newStart.getDate())}T00:00:00`
    }
    try {
      await updateEvent(id, { planned_at: newDateStr })
      // 同步本地数据
      const idx = events.value.findIndex(e => e.id === id)
      if (idx !== -1) events.value[idx] = { ...events.value[idx], planned_at: newDateStr }
      ElMessage.success('活动时间已更新')
    } catch {
      info.revert()
      ElMessage.error('更新失败，已还原')
    }
  },
  dayMaxEvents: 3,
}))

async function loadEvents() {
  loading.value = true
  try {
    const data = await listEvents({
      status: filterStatus.value || undefined,
      event_type: filterType.value || undefined,
      community_id: filterCommunity.value || undefined,
      keyword: filterKeyword.value || undefined,
      page: currentPage.value,
      page_size: pageSize,
        })
    events.value = data.items
    total.value = data.total
  } catch {
    // 错误已由 API 拦截器统一展示，此处仅做状态兜底
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createForm.value = { title: '', event_type: 'offline', community_id: null, planned_at: null, location: '', description: '' }
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
      community_id: createForm.value.community_id || null,
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

async function handleDeleteEvent(row: EventListItem) {
  try {
    await deleteEvent(row.id)
    ElMessage.success('活动已删除')
    await loadEvents()
  } catch {
    ElMessage.error('删除失败，请重试')
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

.empty-state {
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

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.view-toggle {
  margin-left: auto;
}

.community-tag {
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}

.no-community {
  color: #94a3b8;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.action-buttons :deep(.el-button.is-link) {
  height: auto;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.action-buttons :deep(.el-button--danger.is-link) {
  color: var(--red, #ef4444);
  background: transparent;
}

.action-buttons :deep(.el-button--danger.is-link:hover) {
  color: #dc2626;
  background: #fef2f2;
}

.events-table-container {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.events-table-container :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #e2e8f0;
  padding: 14px 0;
}

.events-table-container :deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #f1f5f9;
  padding: 14px 0;
  font-size: 14px;
  color: #1e293b;
}

.events-table-container :deep(.el-table__row) {
  cursor: pointer;
}

.events-table-container :deep(.el-table__row:hover > td.el-table__cell) {
  background: #f8fafc !important;
}

.calendar-container {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
}

/* ===== FullCalendar 深度样式（与 CommunitySandbox 统一） ===== */
:deep(.events-calendar .fc) {
  font-family: inherit;
}

:deep(.events-calendar .fc-toolbar) {
  margin-bottom: 16px !important;
  align-items: center !important;
}
:deep(.events-calendar .fc-toolbar-title) {
  font-size: 15px !important;
  font-weight: 700 !important;
  color: #1e293b;
  letter-spacing: -0.01em;
}

/* 所有按钮基础 */
:deep(.events-calendar .fc-button) {
  background: #fff !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 4px 10px !important;
  border-radius: 7px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
  transition: background 0.13s, border-color 0.13s, color 0.13s !important;
}
:deep(.events-calendar .fc-button:hover:not(:disabled)) {
  background: #f1f5f9 !important;
  border-color: #cbd5e1 !important;
  color: #1e293b !important;
}
:deep(.events-calendar .fc-button.fc-button-active) {
  background: #0095ff !important;
  border-color: #0095ff !important;
  color: #fff !important;
  box-shadow: 0 2px 7px rgba(0,149,255,0.28) !important;
}
:deep(.events-calendar .fc-button:focus) { box-shadow: none !important; }

/* 今天按钮 */
:deep(.events-calendar .fc-today-button) {
  background: rgba(0,149,255,0.08) !important;
  border-color: rgba(0,149,255,0.22) !important;
  color: #0095ff !important;
  font-weight: 600 !important;
  border-radius: 7px !important;
}
:deep(.events-calendar .fc-today-button:hover:not(:disabled)) {
  background: rgba(0,149,255,0.15) !important;
  border-color: #0095ff !important;
}

/* 前/后翻页 */
:deep(.events-calendar .fc-prev-button),
:deep(.events-calendar .fc-next-button) {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  color: #94a3b8 !important;
  padding: 4px 7px !important;
}
:deep(.events-calendar .fc-prev-button:hover:not(:disabled)),
:deep(.events-calendar .fc-next-button:hover:not(:disabled)) {
  background: #f1f5f9 !important;
  border-color: #e2e8f0 !important;
  color: #1e293b !important;
}

/* 表头星期行 */
:deep(.events-calendar .fc-col-header-cell) {
  background: #fff !important;
  border-color: transparent !important;
  padding: 8px 0 6px !important;
}
:deep(.events-calendar .fc-col-header-cell-cushion) {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  text-decoration: none !important;
}
:deep(.events-calendar .fc-col-header) {
  border-bottom: 2px solid #e2e8f0 !important;
}

/* 日期单元格 */
:deep(.events-calendar .fc-daygrid-day) {
  border-color: #f1f5f9 !important;
  transition: background 0.12s;
}
:deep(.events-calendar .fc-daygrid-day:hover:not(.fc-day-today)) {
  background: #fafbfc;
}
:deep(.events-calendar .fc-daygrid-day.fc-day-other .fc-daygrid-day-number) {
  color: #cbd5e1 !important;
}
:deep(.events-calendar .fc-daygrid-day-top) {
  justify-content: flex-end;
}

/* 今天单元格 */
:deep(.events-calendar .fc-day-today) {
  background: linear-gradient(145deg, rgba(0,149,255,0.07) 0%, rgba(0,149,255,0.01) 100%) !important;
}
:deep(.events-calendar .fc-day-today .fc-daygrid-day-number) {
  background: #0095ff !important;
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
:deep(.events-calendar .fc-daygrid-day-number) {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  padding: 4px 6px !important;
  text-decoration: none !important;
}

/* 事件胶囊 */
:deep(.events-calendar .fc-event) {
  font-size: 11px;
  border-radius: 4px !important;
  border: none !important;
  border-left: 3px solid rgba(0,0,0,0.16) !important;
  padding: 1px 5px !important;
  margin: 0 3px 2px !important;
  cursor: pointer !important;
  transition: transform 0.11s, box-shadow 0.11s !important;
}
:deep(.events-calendar .fc-event:hover) {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0,0,0,0.12) !important;
}

/* "更多"链接 */
:deep(.events-calendar .fc-daygrid-more-link) {
  font-size: 10px;
  font-weight: 600;
  color: #0095ff !important;
  background: rgba(0,149,255,0.08);
  border-radius: 3px;
  padding: 1px 5px;
  text-decoration: none !important;
}

/* 周末轻染色 */
:deep(.events-calendar .fc-day-sat:not(.fc-day-today)),
:deep(.events-calendar .fc-day-sun:not(.fc-day-today)) {
  background: rgba(248,250,252,0.6);
}

:deep(.events-calendar .fc-daygrid-day-events) {
  min-height: 1.2em;
}
</style>
