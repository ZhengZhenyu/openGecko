<template>
  <div class="contacts-table-wrap">
    <!-- 批量操作栏（有选中时显示） -->
    <div v-if="selectedRows.length > 0" class="batch-toolbar">
      <span class="batch-count">已选 <strong>{{ selectedRows.length }}</strong> 条</span>
      <el-select v-model="batchStatus" placeholder="选择新状态" size="small" style="width: 140px" clearable>
        <el-option v-for="(lbl, val) in statusLabel" :key="val" :label="lbl" :value="val" />
      </el-select>
      <el-button type="primary" size="small" :disabled="!batchStatus" @click="applyBatch">
        批量修改
      </el-button>
      <el-button size="small" @click="clearSelection">取消选择</el-button>
    </div>

    <!-- 普通工具栏 -->
    <div class="table-toolbar">
      <el-select
        v-model="localStatus"
        placeholder="状态筛选"
        clearable
        size="small"
        style="width: 140px"
        @change="onStatusChange"
      >
        <el-option v-for="(lbl, val) in statusLabel" :key="val" :label="lbl" :value="val" />
      </el-select>
      <slot name="toolbar-extra" />
    </div>

    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="contacts"
      style="width: 100%"
      @selection-change="onSelectionChange"
    >
      <el-table-column type="selection" width="40" />
      <el-table-column label="姓名" min-width="120">
        <template #default="{ row }">{{ row.person?.display_name ?? '-' }}</template>
      </el-table-column>
      <el-table-column label="公司/组织" min-width="120">
        <template #default="{ row }">{{ row.person?.company ?? '-' }}</template>
      </el-table-column>
      <el-table-column label="邮箱" min-width="150">
        <template #default="{ row }">{{ row.person?.email ?? '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="130">
        <template #default="{ row }">
          <el-tag :type="statusTagMap[row.status] ?? 'info'" size="small">
            {{ statusLabel[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="85">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ sourceLabel[row.added_by] ?? row.added_by }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="最近跟进" width="110">
        <template #default="{ row }">
          {{ row.last_contacted_at ? fmtDate(row.last_contacted_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="$emit('follow-up', row)">跟进</el-button>
          <el-select
            :model-value="row.status"
            size="small"
            style="width: 100px"
            @change="(v: string) => $emit('status-change', row, v)"
          >
            <el-option v-for="(lbl, val) in statusLabel" :key="val" :label="lbl" :value="val" />
          </el-select>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="localPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      style="margin-top: 12px; display: flex; justify-content: flex-end"
      @current-change="$emit('page-change', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ContactOut } from '../../api/campaign'

const props = defineProps<{
  contacts: ContactOut[]
  total: number
  page: number
  pageSize: number
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'follow-up', contact: ContactOut): void
  (e: 'status-change', contact: ContactOut, status: string): void
  (e: 'batch-status-change', contactIds: number[], status: string): void
  (e: 'page-change', page: number): void
  (e: 'status-filter', status: string): void
}>()

const tableRef = ref()
const localPage = ref(props.page)
const localStatus = ref('')
const selectedRows = ref<ContactOut[]>([])
const batchStatus = ref('')

watch(() => props.page, (v) => { localPage.value = v })

function onStatusChange(v: string) {
  emit('status-filter', v)
}

function onSelectionChange(rows: ContactOut[]) {
  selectedRows.value = rows
}

function applyBatch() {
  if (!batchStatus.value || selectedRows.value.length === 0) return
  const ids = selectedRows.value.map((r) => r.id)
  emit('batch-status-change', ids, batchStatus.value)
  batchStatus.value = ''
  tableRef.value?.clearSelection()
}

function clearSelection() {
  tableRef.value?.clearSelection()
  batchStatus.value = ''
}

function fmtDate(dt: string) {
  return new Date(dt).toLocaleDateString('zh-CN')
}

const statusLabel: Record<string, string> = {
  pending: '待联系',
  contacted: '已联系',
  blocked: '阻塞中',
}

const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  pending: 'info',
  contacted: 'primary',
  blocked: 'warning',
}

const sourceLabel: Record<string, string> = {
  manual: '手动',
  event_import: '活动导入',
  ecosystem_import: '委员会',
  csv_import: 'CSV',
}
</script>

<style scoped>
.contacts-table-wrap {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.table-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  flex-wrap: wrap;
}

.batch-count {
  font-size: 13px;
  color: #1d4ed8;
  white-space: nowrap;
}
</style>

