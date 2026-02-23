<template>
  <div
    ref="panelRef"
    class="section-card unscheduled-panel"
    :class="{ collapsed: collapsed, 'drop-target-active': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop="isDragging = false"
  >
    <div class="panel-header" @click="$emit('toggle')">
      <span v-if="!collapsed">
        <el-icon><Collection /></el-icon>
        未排期内容
      </span>
      <el-icon :class="{ rotate: collapsed }">
        <ArrowLeft />
      </el-icon>
    </div>
    <div v-if="!collapsed" ref="containerRef" class="panel-body">
      <div
        v-for="item in events"
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
        v-if="events.length === 0"
        description="暂无未排期内容"
        :image-size="60"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Collection, ArrowLeft } from '@element-plus/icons-vue'
import type { ContentCalendarItem } from '../../api/content'

interface Props {
  events: ContentCalendarItem[]
  collapsed: boolean
}

defineProps<Props>()

defineEmits<{
  toggle: []
}>()

const panelRef = ref<HTMLElement>()
const containerRef = ref<HTMLElement>()
const isDragging = ref(false)

defineExpose({
  panelRef,
  containerRef,
})

const STATUS_COLORS: Record<string, string> = {
  draft: '#909399',
  reviewing: '#E6A23C',
  approved: '#0095ff',
  published: '#67C23A',
}

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  reviewing: '审核中',
  approved: '已通过',
  published: '已发布',
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
</script>

<style scoped>
.section-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 16px;
}

.unscheduled-panel {
  width: 320px;
  margin-right: 16px;
  transition: all 0.3s;
}

.unscheduled-panel.collapsed {
  width: 48px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  padding: 8px 0;
}

.panel-header .el-icon {
  transition: transform 0.3s;
}

.panel-header .el-icon.rotate {
  transform: rotate(180deg);
}

.panel-body {
  margin-top: 12px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.unscheduled-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  background: #f8fafc;
  cursor: grab;
  transition: all 0.2s;
}

.unscheduled-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.unscheduled-item:active {
  cursor: grabbing;
}

.item-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 14px;
  color: #1e293b;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-author {
  font-size: 12px;
  color: #64748b;
}

.drop-target-active {
  background: #eff6ff;
  border: 2px dashed #0095ff;
}
</style>
