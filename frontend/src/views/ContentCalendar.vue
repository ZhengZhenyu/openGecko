<template>
  <div class="content-calendar-container">
    <!-- 顶部工具栏 -->
    <div class="page-title">
      <div class="header-left">
        <div>
          <h2>内容日历</h2>
          <p class="subtitle">可视化管理内容排期</p>
        </div>
        <el-tag type="info" size="small" style="margin-left: 12px">
          {{ eventCount }} 条内容
        </el-tag>
      </div>
      <div class="header-actions">
        <el-select
          v-model="statusFilter"
          placeholder="筛选状态"
          clearable
          size="default"
          style="width: 140px; margin-right: 12px"
          @change="refetchEvents"
        >
          <el-option label="全部状态" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="审核中" value="reviewing" />
          <el-option label="已通过" value="approved" />
          <el-option label="已发布" value="published" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="handleCreateContent()">
          新建内容
        </el-button>
      </div>
    </div>

    <!-- 社区未选择提示 -->
    <el-empty
      v-if="!communityStore.currentCommunityId"
      description="请先在顶部选择一个社区"
      :image-size="120"
    />

    <!-- 日历主体 -->
    <div v-else class="calendar-wrapper">
      <!-- 左侧未排期内容面板 -->
      <div
        ref="unscheduledPanelRef"
        class="section-card unscheduled-panel"
        :class="{ collapsed: panelCollapsed, 'drop-target-active': isDraggingOverPanel }"
        @dragover.prevent="isDraggingOverPanel = true"
        @dragleave="isDraggingOverPanel = false"
        @drop="isDraggingOverPanel = false"
      >
        <div class="panel-header" @click="panelCollapsed = !panelCollapsed">
          <span v-if="!panelCollapsed">
            <el-icon><Collection /></el-icon>
            未排期内容
          </span>
          <el-icon :class="{ rotate: panelCollapsed }">
            <ArrowLeft />
          </el-icon>
        </div>
        <div v-if="!panelCollapsed" ref="unscheduledContainerRef" class="panel-body">
          <div
            v-for="item in unscheduledEvents"
            :key="item.id"
            class="unscheduled-item"
            :class="'status-' + item.status"
            :data-event="JSON.stringify({ id: item.id, title: item.title, status: item.status, source_type: item.source_type, author: item.author, category: item.category })"
          >
            <div class="item-dot" :style="{ backgroundColor: getStatusColor(item.status) }" />
            <div class="item-info">
              <div class="item-title">{{ item.title }}</div>
              <div class="item-meta">
                <el-tag :type="getStatusTagType(item.status)" size="small" effect="plain">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
                <span class="item-author">{{ item.author }}</span>
              </div>
            </div>
          </div>
          <el-empty
            v-if="unscheduledEvents.length === 0"
            description="暂无未排期内容"
            :image-size="60"
          />
        </div>
      </div>

      <!-- FullCalendar -->
      <div class="section-card calendar-main">
        <FullCalendar ref="calendarRef" :options="calendarOptions" />
      </div>
    </div>

    <!-- 内容详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedEvent?.title || '内容详情'"
      width="480px"
      class="event-detail-dialog"
    >
      <div v-if="selectedEvent" class="event-detail">
        <div class="detail-row">
          <span class="detail-label">标题</span>
          <span class="detail-value">{{ selectedEvent.title }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">状态</span>
          <el-tag :type="getStatusTagType(selectedEvent.extendedProps.status)" size="small">
            {{ getStatusLabel(selectedEvent.extendedProps.status) }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">来源类型</span>
          <span class="detail-value">{{ getSourceTypeLabel(selectedEvent.extendedProps.source_type) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">作者</span>
          <span class="detail-value">{{ selectedEvent.extendedProps.author || '未设置' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">分类</span>
          <span class="detail-value">{{ selectedEvent.extendedProps.category || '未设置' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">排期时间</span>
          <span class="detail-value">
            {{ selectedEvent.start ? formatDate(selectedEvent.start) : '未排期' }}
          </span>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          type="danger"
          plain
          @click="handleRemoveSchedule"
        >
          取消排期
        </el-button>
        <el-button type="primary" @click="handleEditContent">
          编辑内容
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Collection, ArrowLeft } from '@element-plus/icons-vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin, { Draggable } from '@fullcalendar/interaction'
import listPlugin from '@fullcalendar/list'
import type { CalendarOptions, EventInput, EventDropArg, DateSelectArg, EventClickArg } from '@fullcalendar/core'
import { useCommunityStore } from '../stores/community'
import {
  fetchCalendarEvents,
  updateContentSchedule,
  type ContentCalendarItem,
} from '../api/content'

const router = useRouter()
const communityStore = useCommunityStore()

const calendarRef = ref()
const unscheduledContainerRef = ref<HTMLElement>()
const unscheduledPanelRef = ref<HTMLElement>()
const isDraggingOverPanel = ref(false)
let draggableInstance: InstanceType<typeof Draggable> | null = null
const statusFilter = ref('')
const panelCollapsed = ref(false)
const loading = ref(false)
const detailDialogVisible = ref(false)
const selectedEvent = ref<any>(null)
const calendarEvents = ref<ContentCalendarItem[]>([])
const unscheduledEvents = ref<ContentCalendarItem[]>([])

const eventCount = computed(() => calendarEvents.value.length + unscheduledEvents.value.length)

// ==================== 状态映射 ====================

const STATUS_COLORS: Record<string, string> = {
  draft: '#909399',
  reviewing: '#E6A23C',
  approved: '#0095ff',
  published: '#67C23A',
}

// 浅色调背景色（chip 风格）
const STATUS_PASTELS: Record<string, string> = {
  draft:     '#f1f5f9',
  reviewing: '#fff8ed',
  approved:  '#eff6ff',
  published: '#f0faf4',
}

function getStatusPastel(status: string): string {
  return STATUS_PASTELS[status] || '#f1f5f9'
}

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  reviewing: '审核中',
  approved: '已通过',
  published: '已发布',
}

const SOURCE_TYPE_LABELS: Record<string, string> = {
  contribution: '投稿',
  release_note: '发行说明',
  event_summary: '活动总结',
}

function getStatusColor(status: string): string {
  return STATUS_COLORS[status] || '#909399'
}

function getStatusLabel(status: string): string {
  return STATUS_LABELS[status] || status
}

function getStatusTagType(status: string): 'info' | 'warning' | '' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'warning' | '' | 'success' | 'danger'> = {
    draft: 'info',
    reviewing: 'warning',
    approved: '',
    published: 'success',
  }
  return map[status] || 'info'
}

function getSourceTypeLabel(type: string): string {
  return SOURCE_TYPE_LABELS[type] || type
}

function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * 将 FullCalendar 返回的 Date 转为可靠的排期 ISO 字符串。
 * 从未排期面板拖入月视图时 start 为本地午夜(00:00)，直接 toISOString()
 * 会因 UTC 偏移导致日期倒退一天（例如 UTC+8 00:00 → UTC 前一天 16:00）。
 * 统一修正为本地正午(12:00)再序列化，消除时区跨日问题。
 */
function toScheduleISO(date: Date): string {
  const d = new Date(date)
  if (d.getHours() === 0 && d.getMinutes() === 0 && d.getSeconds() === 0) {
    d.setHours(12, 0, 0, 0)
  }
  return d.toISOString()
}

// ==================== 日历配置 ====================

function transformToEvents(items: ContentCalendarItem[]): EventInput[] {
  return items
    .filter((item) => item.scheduled_publish_at)
    .map((item) => ({
      id: String(item.id),
      title: item.title,
      start: item.scheduled_publish_at!,
      allDay: false,
      backgroundColor: getStatusPastel(item.status),
      borderColor: getStatusColor(item.status),
      textColor: '#1e293b',
      extendedProps: {
        status: item.status,
        source_type: item.source_type,
        author: item.author,
        category: item.category,
        content_id: item.id,
      },
    }))
}

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-cn',
  headerToolbar: {
    left: 'prev,today,next',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
  },
  buttonText: {
    today: '今天',
    month: '月',
    week: '周',
    day: '日',
    list: '列表',
  },
  // 交互功能
  editable: true,
  droppable: true,
  selectable: true,
  selectMirror: true,
  dayMaxEvents: 4,
  eventMaxStack: 3,
  nowIndicator: true,

  // 事件
  events: transformToEvents(calendarEvents.value),
  
  // 日期范围变化（切换月份/视图时获取数据）
  datesSet: handleDatesSet,
  // 拖拽移动事件
  eventDrop: handleEventDrop,
  // 拖拽结束（检测是否拖回未排期面板）
  eventDragStop: handleEventDragStop,
  // 点击事件
  eventClick: handleEventClick,
  // 选择日期范围
  select: handleDateSelect,
  // 外部拖入
  eventReceive: handleEventReceive,
  // 事件渲染
  eventContent: renderEventContent,

  // 样式
  height: 'auto',
  contentHeight: 'auto',
  aspectRatio: 1.8,
  fixedWeekCount: false,
  showNonCurrentDates: true,
  handleWindowResize: true,
}))

// ==================== 事件处理 ====================

async function handleDatesSet(info: { startStr: string; endStr: string }) {
  await loadEvents(info.startStr, info.endStr)
}

async function loadEvents(start: string, end: string) {
  if (!communityStore.currentCommunityId) return
  loading.value = true
  try {
    const items = await fetchCalendarEvents({
      start: start.slice(0, 10),
      end: end.slice(0, 10),
      status: statusFilter.value || undefined,
    })

    // 分离已排期和未排期
    calendarEvents.value = items.filter((i) => i.scheduled_publish_at)
    unscheduledEvents.value = items.filter((i) => !i.scheduled_publish_at)
  } catch (err: any) {
    ElMessage.error('加载日历数据失败: ' + (err?.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function handleEventDrop(info: EventDropArg) {
  const contentId = Number(info.event.id)
  const newDate = info.event.start

  if (!newDate) {
    info.revert()
    return
  }

  try {
    await updateContentSchedule(contentId, toScheduleISO(newDate))
    ElMessage.success('发布时间已更新')
  } catch (err: any) {
    info.revert()
    ElMessage.error('更新失败: ' + (err?.response?.data?.detail || err.message))
  }
}

async function handleEventDragStop(info: any) {
  // 检测事件是否被拖到了未排期面板区域
  const panelEl = unscheduledPanelRef.value
  if (!panelEl) return

  const rect = panelEl.getBoundingClientRect()
  const { clientX, clientY } = info.jsEvent
  const isOverPanel =
    clientX >= rect.left && clientX <= rect.right &&
    clientY >= rect.top && clientY <= rect.bottom

  if (isOverPanel) {
    const contentId = Number(info.event.extendedProps.content_id || info.event.id)
    try {
      await updateContentSchedule(contentId, null)
      ElMessage.success(`"${info.event.title}" 已取消排期`)
      await refetchEvents()
    } catch (err: any) {
      ElMessage.error('取消排期失败: ' + (err?.response?.data?.detail || err.message))
    }
  }
  isDraggingOverPanel.value = false
}

function handleEventClick(info: EventClickArg) {
  selectedEvent.value = {
    id: info.event.id,
    title: info.event.title,
    start: info.event.start,
    extendedProps: info.event.extendedProps,
  }
  detailDialogVisible.value = true
}

function handleDateSelect(info: DateSelectArg) {
  createForm.title = ''
  createForm.source_type = 'contribution'
  createForm.author = ''
  createForm.scheduled_publish_at = info.startStr
  createDialogVisible.value = true
}

function initDraggable() {
  if (draggableInstance) {
    draggableInstance.destroy()
    draggableInstance = null
  }
  if (!unscheduledContainerRef.value) return
  draggableInstance = new Draggable(unscheduledContainerRef.value, {
    itemSelector: '.unscheduled-item',
    eventData: (el) => {
      const data = JSON.parse(el.getAttribute('data-event') || '{}')
      return {
        id: String(data.id),
        title: data.title,
        backgroundColor: getStatusPastel(data.status),
        borderColor: getStatusColor(data.status),
        textColor: '#1e293b',
        extendedProps: { ...data },
      }
    },
  })
}

async function handleEventReceive(info: any) {
  const contentId = Number(info.event.extendedProps.id || info.event.id)
  const newDate = info.event.start
  if (!newDate) {
    info.revert()
    return
  }
  try {
    await updateContentSchedule(contentId, toScheduleISO(newDate))
    ElMessage.success(`"${info.event.title}" 已排期`)
    await refetchEvents()
  } catch (err: any) {
    info.revert()
    ElMessage.error('排期失败: ' + (err?.response?.data?.detail || err.message))
  }
}

function renderEventContent(arg: any) {
  const status = arg.event.extendedProps.status
  const author = arg.event.extendedProps.author
  const timeText = arg.timeText

  const accentColor = getStatusColor(status)
  return {
    html: `
      <div class="fc-event-custom" style="border-left-color:${accentColor}">
        <div class="fc-event-info">
          <span class="fc-event-title">${arg.event.title}</span>
          ${author || timeText ? `<span class="fc-event-meta" style="color:${accentColor}">${author ? author : ''}${timeText ? ' · ' + timeText : ''}</span>` : ''}
        </div>
      </div>
    `,
  }
}

// ==================== 操作 ====================

function handleCreateContent() {
  router.push('/contents/new')
}

function handleEditContent() {
  if (selectedEvent.value) {
    const id = selectedEvent.value.extendedProps.content_id || selectedEvent.value.id
    detailDialogVisible.value = false
    router.push({ name: 'ContentEdit', params: { id } })
  }
}

async function handleRemoveSchedule() {
  if (!selectedEvent.value) return
  const id = selectedEvent.value.extendedProps.content_id || selectedEvent.value.id
  try {
    await updateContentSchedule(Number(id), null)
    ElMessage.success('排期已取消')
    detailDialogVisible.value = false
    await refetchEvents()
  } catch (err: any) {
    ElMessage.error('操作失败: ' + (err?.response?.data?.detail || err.message))
  }
}

async function refetchEvents() {
  const calendarApi = calendarRef.value?.getApi()
  if (calendarApi) {
    const view = calendarApi.view
    await loadEvents(view.activeStart.toISOString(), view.activeEnd.toISOString())
  }
}

// 监听社区切换
watch(
  () => communityStore.currentCommunityId,
  () => {
    refetchEvents()
  }
)

// 当未排期内容列表变化时重新初始化 Draggable
watch(
  () => unscheduledEvents.value,
  () => {
    nextTick(() => initDraggable())
  }
)

// 面板展开/收起时重新初始化
watch(panelCollapsed, (collapsed) => {
  if (!collapsed) {
    nextTick(() => initDraggable())
  }
})

onMounted(() => {
  nextTick(() => initDraggable())
})

onBeforeUnmount(() => {
  if (draggableInstance) {
    draggableInstance.destroy()
    draggableInstance = null
  }
})
</script>

<style lang="scss">
.content-calendar-container {
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

  padding: 32px 40px 60px;
  max-width: 1440px;
  margin: 0 auto;
}

// ==================== 页面标题 ====================

.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;

  h2 {
    margin: 0 0 6px;
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }

  .subtitle {
    margin: 0;
    color: var(--text-secondary);
    font-size: 15px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-actions {
    display: flex;
    align-items: center;
  }
}

// ==================== 通用卡片样式 ====================

.section-card {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

// ==================== 主体布局 ====================

.calendar-wrapper {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

// ==================== 左侧未排期面板 ====================

.unscheduled-panel {
  width: 260px;
  min-width: 260px;
  transition: all 0.3s ease;
  overflow: hidden;
  padding: 0;

  &.drop-target-active {
    background: #eff6ff;
    border: 2px dashed var(--blue);
    box-shadow: 0 0 12px rgba(0, 149, 255, 0.15);
  }

  &.collapsed {
    width: 40px;
    min-width: 40px;

    .panel-header {
      justify-content: center;
      padding: 12px 8px;
    }
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    font-weight: 600;
    font-size: 14px;
    color: var(--text-primary);
    border-bottom: 1px solid #f1f5f9;
    cursor: pointer;
    user-select: none;
    gap: 8px;

    &:hover {
      background: #f8fafc;
    }

    .el-icon {
      transition: transform 0.3s;
      &.rotate {
        transform: rotate(180deg);
      }
    }
  }

  .panel-body {
    max-height: calc(100vh - 240px);
    overflow-y: auto;
    padding: 8px;
  }
}

.unscheduled-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 6px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid var(--border);
  cursor: grab;
  transition: all 0.2s ease;

  &:hover {
    background: #eff6ff;
    box-shadow: var(--shadow);
  }

  &:active,
  &.fc-dragging {
    cursor: grabbing;
    opacity: 0.4;
    box-shadow: var(--shadow-hover);
  }

  &.status-draft { border-left-color: var(--text-muted); }
  &.status-reviewing { border-left-color: var(--orange); }
  &.status-approved { border-left-color: var(--blue); }
  &.status-published { border-left-color: var(--green); }

  .item-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
  }

  .item-info {
    flex: 1;
    min-width: 0;

    .item-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .item-meta {
      display: flex;
      align-items: center;
      gap: 6px;

      .item-author {
        font-size: 11px;
        color: var(--text-muted);
      }
    }
  }
}

// ==================== 日历主体 ====================

.calendar-main {
  flex: 1;
  background: #ffffff;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  padding: 24px;
  overflow: hidden;
}

// ==================== FullCalendar 深度样式定制 ====================

.fc {
  font-family: inherit;

  // ── 工具栏 ──────────────────────────────────────────────────────
  .fc-toolbar {
    margin-bottom: 20px !important;
    align-items: center !important;
    gap: 8px;

    .fc-toolbar-title {
      font-size: 17px !important;
      font-weight: 700 !important;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }
  }

  // 所有按钮基础重置
  .fc-button {
    background: #fff !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 5px 13px !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: background 0.14s, border-color 0.14s, color 0.14s, box-shadow 0.14s !important;
    line-height: 1.5 !important;

    &:hover:not(:disabled) {
      background: #f1f5f9 !important;
      border-color: #cbd5e1 !important;
      color: var(--text-primary) !important;
      box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
    }

    &.fc-button-active {
      background: var(--blue) !important;
      border-color: var(--blue) !important;
      color: #fff !important;
      box-shadow: 0 2px 8px rgba(0,149,255,0.28) !important;
    }

    &:disabled {
      opacity: 0.4 !important;
    }

    &:focus { box-shadow: none !important; }
  }

  // 前/后翻页按钮：纯图标，无边框
  .fc-prev-button,
  .fc-next-button {
    padding: 5px 9px !important;
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
    color: var(--text-muted) !important;

    &:hover:not(:disabled) {
      background: #f1f5f9 !important;
      border-color: var(--border) !important;
      color: var(--text-primary) !important;
      box-shadow: none !important;
    }
  }

  // 今天按钮：蓝色 ghost
  .fc-today-button {
    background: rgba(0,149,255,0.08) !important;
    border-color: rgba(0,149,255,0.25) !important;
    color: var(--blue) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;

    &:hover:not(:disabled) {
      background: rgba(0,149,255,0.14) !important;
      border-color: var(--blue) !important;
    }
  }

  // 视图切换器：胶囊组
  .fc-button-group {
    background: #f1f5f9;
    border-radius: 10px;
    padding: 3px;
    gap: 2px;
    display: inline-flex;
    border: none !important;
    box-shadow: none !important;

    .fc-button {
      border-radius: 7px !important;
      border: none !important;
      background: transparent !important;
      box-shadow: none !important;
      padding: 4px 12px !important;
      color: var(--text-secondary) !important;

      &:hover:not(:disabled) {
        background: rgba(255,255,255,0.7) !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
      }

      &.fc-button-active {
        background: #fff !important;
        color: var(--blue) !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.10) !important;
        border: none !important;
      }
    }
  }

  // ── 表头（星期行） ───────────────────────────────────────────────
  .fc-col-header {
    border-bottom: 2px solid #e2e8f0 !important;
  }

  .fc-col-header-cell {
    padding: 10px 0 8px !important;
    background: #fff !important;
    border-color: transparent !important;

    .fc-col-header-cell-cushion {
      font-weight: 700;
      color: #94a3b8;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      text-decoration: none !important;
    }
  }

  // 周末列轻染色
  .fc-day-sat .fc-col-header-cell-cushion,
  .fc-day-sun .fc-col-header-cell-cushion {
    color: #c4b5fd;
  }

  // ── 月格单元格 ──────────────────────────────────────────────────
  .fc-daygrid-day {
    border-color: #f1f5f9 !important;
    transition: background 0.12s;
    min-height: 110px;
    vertical-align: top;

    &:hover:not(.fc-day-today) {
      background: #fafbfc;
    }

    // 非当前月日期
    &.fc-day-other {
      .fc-daygrid-day-number { color: #cbd5e1 !important; }
    }

    // 今天
    &.fc-day-today {
      background: linear-gradient(160deg, rgba(0,149,255,0.07) 0%, rgba(0,149,255,0.01) 100%) !important;

      .fc-daygrid-day-number {
        background: var(--blue);
        color: #fff !important;
        border-radius: 14px;
        padding: 2px 8px !important;
        margin: 5px 6px;
        font-weight: 700;
        white-space: nowrap;
        box-shadow: 0 2px 8px rgba(0,149,255,0.35);
        display: inline-block;
        line-height: 1.6;
        box-sizing: border-box;
      }
    }
  }

  .fc-daygrid-day-number {
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    padding: 5px 8px !important;
    text-decoration: none !important;
    transition: color 0.12s;
  }

  // 日期顶部 frame
  .fc-daygrid-day-top {
    justify-content: flex-end;
  }

  // ── 事件胶囊（chip 风格：浅色底 + 有色左边框 + 深色文字）────────
  .fc-event {
    border-radius: 5px !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-left-width: 3px !important;
    padding: 0 !important;
    margin: 0 4px 3px !important;
    font-size: 12px !important;
    cursor: pointer !important;
    transition: transform 0.12s, box-shadow 0.12s !important;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.10) !important;
    }
  }

  // 自定义事件内容
  .fc-event-custom {
    display: flex;
    align-items: center;
    padding: 3px 7px;
    width: 100%;
    overflow: hidden;

    .fc-event-dot {
      display: none;
    }

    .fc-event-info {
      display: flex;
      flex-direction: column;
      min-width: 0;
      flex: 1;

      .fc-event-title {
        font-size: 12px;
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.5;
        color: #1e293b;
      }

      .fc-event-meta {
        font-size: 10px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.3;
        font-weight: 500;
      }
    }
  }

  // "更多"气泡链接
  .fc-daygrid-more-link {
    font-size: 11px;
    font-weight: 600;
    color: var(--blue);
    background: rgba(0,149,255,0.08);
    border-radius: 4px;
    padding: 1px 6px;
    margin: 0 4px;
    text-decoration: none !important;

    &:hover {
      background: rgba(0,149,255,0.16);
    }
  }

  // ── 时间网格视图 ─────────────────────────────────────────────────
  .fc-timegrid-slot {
    height: 44px !important;
    border-color: #f1f5f9 !important;
  }

  .fc-timegrid-slot-minor {
    border-color: #f8fafc !important;
    border-top-style: dashed !important;
  }

  .fc-timegrid-slot-label-cushion {
    font-size: 11px;
    color: #94a3b8;
    font-weight: 500;
  }

  .fc-timegrid-col.fc-day-today {
    background: linear-gradient(180deg, rgba(0,149,255,0.04) 0%, transparent 100%) !important;
  }

  // ── 列表视图 ─────────────────────────────────────────────────────
  .fc-list {
    border: none;
    border-radius: var(--radius);
    overflow: hidden;

    .fc-list-day {
      th { border: none !important; }
    }

    .fc-list-day-cushion {
      background: linear-gradient(90deg, #f8fafc 0%, #fff 100%) !important;
      padding: 9px 20px !important;
      font-size: 12px !important;
      font-weight: 700;
      color: var(--text-primary) !important;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border-bottom: 1px solid #f1f5f9;
    }

    .fc-list-event {
      cursor: pointer;
      transition: background 0.12s;

      td { border-color: #f8fafc !important; }

      &:hover td {
        background: #f0f9ff;
      }
    }

    .fc-list-event-graphic {
      padding: 12px 8px 12px 20px !important;
    }

    .fc-list-event-dot {
      border-radius: 50%;
      border-width: 6px !important;
    }

    .fc-list-event-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-primary);
    }

    .fc-list-event-time {
      font-size: 12px;
      color: var(--text-muted);
    }
  }

  // ── Popover（更多事件展开框） ────────────────────────────────────
  .fc-popover {
    border-radius: 14px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid rgba(226,232,240,0.8);
    overflow: hidden;

    .fc-popover-header {
      background: linear-gradient(135deg, #f8fafc 0%, #fff 100%);
      padding: 10px 16px;
      font-weight: 700;
      font-size: 13px;
      color: var(--text-primary);
      border-bottom: 1px solid #f1f5f9;
    }

    .fc-popover-body {
      padding: 6px 8px 8px;
    }
  }

  // ── 日期范围选中高亮 ─────────────────────────────────────────────
  .fc-highlight {
    background: rgba(0, 149, 255, 0.06) !important;
    border: 2px dashed rgba(0,149,255,0.4) !important;
    border-radius: 6px;
  }

  // ── 拖拽幽灵 ────────────────────────────────────────────────────
  .fc-event-mirror {
    opacity: 0.55;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18) !important;
    transform: rotate(1deg) scale(1.02);
  }

  // ── 周末列背景 ──────────────────────────────────────────────────
  .fc-day-sat,
  .fc-day-sun {
    &:not(.fc-day-today) {
      background: rgba(248,250,252,0.6);
    }
  }
}

// ==================== 弹窗样式 ====================

.event-detail-dialog {
  .event-detail {
    .detail-row {
      display: flex;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #f1f5f9;

      &:last-child {
        border-bottom: none;
      }

      .detail-label {
        width: 80px;
        flex-shrink: 0;
        color: var(--text-muted);
        font-size: 13px;
      }

      .detail-value {
        color: var(--text-primary);
        font-size: 14px;
      }
    }
  }
}

// ==================== 响应式 ====================

@media (max-width: 1200px) {
  .content-calendar-container {
    padding: 28px 24px;
  }

  .unscheduled-panel {
    width: 220px;
    min-width: 220px;
  }
}

@media (max-width: 768px) {
  .content-calendar-container {
    padding: 20px 16px;
  }

  .calendar-wrapper {
    flex-direction: column;
  }

  .unscheduled-panel {
    width: 100% !important;
    min-width: 100% !important;

    .panel-body {
      max-height: 200px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .unscheduled-item {
      width: calc(50% - 4px);
    }
  }

  .calendar-main {
    padding: 16px;
  }

  .fc .fc-toolbar {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
