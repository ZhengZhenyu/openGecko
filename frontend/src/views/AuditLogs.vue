<template>
  <div class="audit-logs-view">
    <div class="page-title-row">
      <div>
        <h2>审计日志</h2>
        <p class="subtitle">查看所有用户操作记录，支持筛选与分页</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="section-card filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="动作">
          <el-input
            v-model="filters.action"
            placeholder="如 create_content"
            clearable
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="filters.resource_type" placeholder="全部" clearable style="width: 140px">
            <el-option value="content" label="内容" />
            <el-option value="committee" label="委员会" />
            <el-option value="meeting" label="会议" />
            <el-option value="member" label="成员" />
            <el-option value="channel" label="渠道" />
            <el-option value="community" label="社区" />
            <el-option value="user" label="用户" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input
            v-model="filters.username"
            placeholder="模糊搜索"
            clearable
            style="width: 140px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 日志表格 -->
    <div class="section-card">
      <el-table
        v-loading="loading"
        :data="logs"
        style="width: 100%"
        :row-class-name="rowClass"
      >
        <el-table-column label="时间" prop="created_at" width="170" fixed>
          <template #default="{ row }">
            <span class="time-cell">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作人" prop="username" width="130">
          <template #default="{ row }">
            <div>
              <div class="user-name">{{ row.full_name || row.username }}</div>
              <div class="user-sub">@{{ row.username }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="动作" prop="action" width="180">
          <template #default="{ row }">
            <span class="action-badge" :class="actionClass(row.action)">{{ row.action }}</span>
          </template>
        </el-table-column>

        <el-table-column label="资源类型" prop="resource_type" width="110">
          <template #default="{ row }">
            <span class="resource-badge">{{ row.resource_type || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="资源 ID" prop="resource_id" width="90" align="center">
          <template #default="{ row }">
            <span class="id-cell">{{ row.resource_id ?? '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="社区 ID" prop="community_id" width="90" align="center">
          <template #default="{ row }">
            <span class="id-cell">{{ row.community_id ?? '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="IP 地址" prop="ip_address" width="130">
          <template #default="{ row }">
            <span class="mono">{{ row.ip_address || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="详情" min-width="200">
          <template #default="{ row }">
            <span v-if="!row.details" class="text-muted">—</span>
            <el-tooltip
              v-else
              :content="JSON.stringify(row.details, null, 2)"
              placement="left"
              :max-width="400"
            >
              <span class="details-preview mono">{{ summariseDetails(row.details) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <span class="total-hint">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="filters.page"
          v-model:page-size="filters.page_size"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="sizes, prev, pager, next"
          @change="loadLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { getAuditLogs, type AuditLogItem } from '../api/admin'

const loading = ref(false)
const logs = ref<AuditLogItem[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

const filters = ref({
  action: '',
  resource_type: '',
  username: '',
  page: 1,
  page_size: 20,
})

async function loadLogs() {
  loading.value = true
  try {
    const params: Record<string, string | number> = {
      page: filters.value.page,
      page_size: filters.value.page_size,
    }
    if (filters.value.action)        params.action = filters.value.action
    if (filters.value.resource_type) params.resource_type = filters.value.resource_type
    if (filters.value.username)      params.username = filters.value.username
    if (dateRange.value?.[0])        params.from_date = dateRange.value[0]
    if (dateRange.value?.[1])        params.to_date = dateRange.value[1]

    const res = await getAuditLogs(params as any)
    logs.value = res.items
    total.value = res.total
  } catch { /* ignore */ } finally {
    loading.value = false
  }
}

function handleSearch() {
  filters.value.page = 1
  loadLogs()
}

function resetFilters() {
  filters.value = { action: '', resource_type: '', username: '', page: 1, page_size: 20 }
  dateRange.value = null
  loadLogs()
}

onMounted(loadLogs)
watch(dateRange, () => {
  filters.value.page = 1
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function summariseDetails(d: Record<string, unknown> | null): string {
  if (!d) return '—'
  const keys = Object.keys(d).slice(0, 3)
  return keys.map(k => `${k}: ${JSON.stringify(d[k])}`).join(', ')
}

function actionClass(action: string): string {
  if (action.startsWith('create')) return 'action-create'
  if (action.startsWith('update') || action.startsWith('edit')) return 'action-update'
  if (action.startsWith('delete') || action.startsWith('remove')) return 'action-delete'
  if (action.startsWith('publish') || action.startsWith('approve')) return 'action-publish'
  return 'action-default'
}

function rowClass({ row }: { row: AuditLogItem }) {
  if (row.action.startsWith('delete')) return 'row-danger'
  return ''
}
</script>

<style scoped>
.audit-logs-view {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title-row h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-title-row .subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}

.section-card:hover { box-shadow: var(--shadow-hover); }

.filter-card {
  padding: 20px 28px 8px;
}

/* ── 单元格样式 ─────────────────────────────── */
.time-cell {
  font-size: 12px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.user-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 1px;
}

/* 动作标签 */
.action-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: 'SF Mono', Monaco, monospace;
}

.action-create  { background: #f0fdf4; color: #15803d; }
.action-update  { background: #eff6ff; color: #1d4ed8; }
.action-delete  { background: #fef2f2; color: #dc2626; }
.action-publish { background: #fffbeb; color: #b45309; }
.action-default { background: #f1f5f9; color: #64748b; }

.resource-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  background: #f1f5f9;
  color: var(--text-secondary);
  border-radius: 6px;
}

.id-cell {
  font-size: 13px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.mono {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.details-preview {
  cursor: help;
  text-decoration: underline;
  text-decoration-style: dotted;
  text-underline-offset: 3px;
  color: var(--text-secondary);
  font-size: 12px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
}

.text-muted { color: var(--text-muted); }

/* ── 分页栏 ─────────────────────────────────── */
.pagination-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
}

.total-hint {
  font-size: 13px;
  color: var(--text-muted);
}

/* ── 表格 Element Plus 覆盖 ─────────────────── */
:deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}

:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
}

:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

:deep(.el-table .row-danger > td) {
  background: #fff8f8;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
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
  border: 1px solid var(--border);
  color: var(--text-primary);
}

:deep(.el-button--default:hover) {
  background: #f8fafc;
  border-color: #cbd5e1;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

@media (max-width: 1200px) {
  .audit-logs-view { padding: 28px 24px; }
}

@media (max-width: 734px) {
  .audit-logs-view { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
}
</style>
