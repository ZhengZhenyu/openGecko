<template>
  <el-dialog
    :model-value="visible"
    :title="event?.title || '内容详情'"
    width="480px"
    class="event-detail-dialog"
    @close="emit('close')"
    @update:model-value="handleUpdateVisible"
  >
    <div v-if="event" class="event-detail">
      <div class="detail-row">
        <span class="detail-label">标题</span>
        <span class="detail-value">{{ event.title }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">状态</span>
        <el-tag :type="getStatusTagType(getStatus(event))" size="small">
          {{ getStatusLabel(getStatus(event)) }}
        </el-tag>
      </div>
      <div class="detail-row">
        <span class="detail-label">来源类型</span>
        <span class="detail-value">{{ getSourceTypeLabel(getSourceType(event)) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">作者</span>
        <span class="detail-value">{{ getAuthor(event) || '未设置' }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">分类</span>
        <span class="detail-value">{{ getCategory(event) || '未设置' }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">排期时间</span>
        <span class="detail-value">
          {{ event.start ? formatDate(event.start) : '未排期' }}
        </span>
      </div>
    </div>
    <template #footer>
      <el-button @click="$emit('close')">关闭</el-button>
      <el-button
        type="danger"
        plain
        @click="$emit('remove-schedule')"
      >
        取消排期
      </el-button>
      <el-button type="primary" @click="$emit('edit-content')">
        编辑内容
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  event: EventInputEvent | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
  'remove-schedule': []
  'edit-content': []
}>()

function handleUpdateVisible(value: boolean) {
  emit('update:visible', value)
}

interface EventInputEvent {
  id: string
  title: string
  start: Date | string
  extendedProps?: {
    status?: string
    source_type?: string
    author?: string
    category?: string
  }
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
    'minute': '2-digit',
  })
}

function getStatus(event: EventInputEvent): string {
  return event.extendedProps?.status || ''
}

function getSourceType(event: EventInputEvent): string {
  return event.extendedProps?.source_type || ''
}

function getAuthor(event: EventInputEvent): string {
  return event.extendedProps?.author || ''
}

function getCategory(event: EventInputEvent): string {
  return event.extendedProps?.category || ''
}
</script>

<style scoped>
.event-detail {
  padding: 8px 0;
}

.detail-row {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  width: 100px;
  font-weight: 500;
  color: #64748b;
  font-size: 14px;
}

.detail-value {
  flex: 1;
  color: #1e293b;
  font-size: 14px;
}
</style>
