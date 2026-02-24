<template>
  <div class="content-list">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-title">
        <div>
          <h2>内容管理</h2>
          <p class="subtitle">管理和组织社区内容</p>
        </div>
        <div class="actions">
          <el-upload
            :show-file-list="false"
            :before-upload="handleUpload"
            accept=".docx,.md,.markdown"
          >
            <el-button type="success" :icon="Upload">上传文件</el-button>
          </el-upload>
          <el-button type="primary" :icon="Plus" @click="$router.push('/contents/new')">新建内容</el-button>
        </div>
      </div>

      <div class="section-card filter-section">
        <div class="filters">
          <el-input v-model="keyword" placeholder="搜索标题..." clearable style="width: 240px" @clear="loadData" @keyup.enter="loadData" />
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadData" style="width: 140px">
            <el-option label="草稿" value="draft" />
            <el-option label="审核中" value="reviewing" />
            <el-option label="已通过" value="approved" />
            <el-option label="已发布" value="published" />
          </el-select>
          <el-select v-model="filterSource" placeholder="来源筛选" clearable @change="loadData" style="width: 140px">
            <el-option label="社区投稿" value="contribution" />
            <el-option label="Release Note" value="release_note" />
            <el-option label="活动总结" value="event_summary" />
          </el-select>
          <el-select v-model="filterCommunity" placeholder="社区筛选" clearable @change="loadData" style="width: 160px">
            <el-option
              v-for="c in authStore.communities"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </div>
      </div>

      <div class="section-card">
        <el-table :data="contents" v-loading="loading" stripe>
          <el-table-column prop="title" label="标题" min-width="240">
            <template #default="{ row }">
              <router-link :to="`/contents/${row.id}/edit`" class="title-link">{{ row.title }}</router-link>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="来源" width="120">
            <template #default="{ row }">{{ sourceLabel(row.source_type) }}</template>
          </el-table-column>
          <el-table-column prop="author" label="作者" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="work_status" label="工作状态" width="100">
            <template #default="{ row }">
              <el-tag :type="workStatusType(row.work_status)" size="small">
                {{ workStatusLabel(row.work_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="community_id" label="关联社区" width="140">
            <template #default="{ row }">
              <el-tooltip
                v-if="row.community_id"
                :content="authStore.getCommunityById(row.community_id)?.name || `社区 #${row.community_id}`"
                placement="top"
                :show-after="300"
              >
                <span class="community-tag">
                  {{ authStore.getCommunityById(row.community_id)?.name || `#${row.community_id}` }}
                </span>
              </el-tooltip>
              <span v-else class="no-community">—</span>
            </template>
          </el-table-column>
          <el-table-column label="责任人" width="180">
            <template #default="{ row }">
              <div v-if="row.assignee_names?.length" class="assignee-chips">
                <span
                  v-for="name in row.assignee_names.slice(0, 2)"
                  :key="name"
                  class="assignee-chip"
                >{{ name }}</span>
                <span v-if="row.assignee_names.length > 2" class="assignee-more">
                  +{{ row.assignee_names.length - 2 }}
                </span>
              </div>
              <span v-else class="no-assignee">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" link type="primary" @click="$router.push(`/contents/${row.id}/edit`)">编辑</el-button>
                <el-button size="small" link type="primary" @click="$router.push(`/publish/${row.id}`)">发布</el-button>
                <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
                  <template #reference>
                    <el-button size="small" link type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="total > pageSize"
          style="margin-top: 16px; justify-content: flex-end"
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { fetchContents, deleteContent, uploadFile, type ContentListItem } from '../api/content'
import { useRouter } from 'vue-router'
import { useCommunityStore } from '../stores/community'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const communityStore = useCommunityStore()
const authStore = useAuthStore()
const contents = ref<ContentListItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const filterStatus = ref('')
const filterSource = ref('')
const filterCommunity = ref<number | null>(null)

async function loadData() {
  loading.value = true
  try {
    const res = await fetchContents({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      source_type: filterSource.value || undefined,
      keyword: keyword.value || undefined,
      community_id: filterCommunity.value || undefined,
    })
    contents.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handlePageChange(p: number) {
  page.value = p
  loadData()
}

async function handleUpload(file: File) {
  try {
    const content = await uploadFile(file)
    ElMessage.success(`文件 "${file.name}" 上传成功`)
    router.push(`/contents/${content.id}/edit`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  }
  return false
}

async function handleDelete(id: number) {
  await deleteContent(id)
  ElMessage.success('已删除')
  loadData()
}

function sourceLabel(s: string) {
  const map: Record<string, string> = { contribution: '社区投稿', release_note: 'Release Note', event_summary: '活动总结' }
  return map[s] || s
}

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布' }
  return map[s] || s
}

function statusType(s: string) {
  const map: Record<string, string> = { draft: 'info', reviewing: 'warning', approved: 'success', published: '' }
  return (map[s] || 'info') as any
}

function workStatusLabel(s: string) {
  const map: Record<string, string> = { 
    planning: '计划中', 
    in_progress: '实施中', 
    completed: '已完成' 
  }
  return map[s] || s
}

function workStatusType(s: string) {
  const map: Record<string, string> = { 
    planning: 'info', 
    in_progress: 'warning', 
    completed: 'success' 
  }
  return (map[s] || 'info') as any
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadData()
  }
})

// Watch for community changes
watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) {
      loadData()
    }
  }
)
</script>

<style scoped>
/* LFX Insights Light Theme - Content List */
.content-list {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --bg-card: #ffffff;
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
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
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
  font-size: 15px;
  color: var(--text-secondary);
}

.actions {
  display: flex;
  gap: 10px;
}

.actions :deep(.el-button) {
  height: 40px;
  padding: 0 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.actions :deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

.actions :deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

.actions :deep(.el-button--success) {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.actions :deep(.el-button--success:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

/* Section Card */
.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.section-card:hover {
  box-shadow: var(--shadow-hover);
}

/* Filter */
.filter-section {
  padding: 16px 20px;
  margin-bottom: 16px;
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filters :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px var(--border);
}

.filters :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

.filters :deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: 14px;
}

.filters :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

/* Table */
.section-card :deep(.el-table) {
  color: var(--text-primary);
  font-size: 14px;
}

.section-card :deep(.el-table::before) {
  display: none;
}

.section-card :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
  padding: 14px 0;
}

.section-card :deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #f1f5f9;
  padding: 14px 0;
}

.section-card :deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

.community-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  color: #1d4ed8;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 5px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}

.no-community {
  color: var(--text-muted);
  font-size: 13px;
}

.assignee-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.assignee-chip {
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  color: #1d4ed8;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 5px;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assignee-more {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.no-assignee {
  color: var(--text-muted);
  font-size: 13px;
}

.title-link {
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s ease;
}

.title-link:hover {
  color: var(--blue);
}

/* Tags */
.section-card :deep(.el-tag) {
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  border: none;
}

.section-card :deep(.el-tag--info) {
  background: #f1f5f9;
  color: var(--text-secondary);
}

.section-card :deep(.el-tag--warning) {
  background: #fffbeb;
  color: #b45309;
}

.section-card :deep(.el-tag--success) {
  background: #f0fdf4;
  color: #15803d;
}

.section-card :deep(.el-tag--primary) {
  background: #eff6ff;
  color: #1d4ed8;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.section-card :deep(.el-button) {
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.action-buttons :deep(.el-button.is-link) {
  height: auto;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.action-buttons :deep(.el-button--primary.is-link) {
  color: var(--blue);
  background: transparent;
}

.action-buttons :deep(.el-button--primary.is-link:hover) {
  color: #0080e6;
  background: #eff6ff;
}

.action-buttons :deep(.el-button--danger.is-link) {
  color: var(--red);
  background: transparent;
}

.action-buttons :deep(.el-button--danger.is-link:hover) {
  color: #dc2626;
  background: #fef2f2;
}

.section-card :deep(.el-button--small) {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.section-card :deep(.el-button--small:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.section-card :deep(.el-button--primary) {
  background: var(--blue);
  color: white;
  border: none;
}

.section-card :deep(.el-button--primary:hover) {
  background: #0080e6;
}

.section-card :deep(.el-button--danger) {
  background: #fef2f2;
  color: var(--red);
  border: 1px solid #fecaca;
}

.section-card :deep(.el-button--danger:hover) {
  background: #fee2e2;
}

/* Pagination */
.section-card :deep(.el-pagination) {
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.section-card :deep(.el-pagination .btn-prev),
.section-card :deep(.el-pagination .btn-next),
.section-card :deep(.el-pagination .el-pager li) {
  border-radius: 6px;
  font-weight: 500;
}

.section-card :deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}

/* Empty */
:deep(.el-empty) {
  padding: 60px;
}

:deep(.el-empty__description) {
  color: var(--text-secondary);
  font-size: 14px;
}

/* Responsive */
@media (max-width: 1200px) {
  .content-list {
    padding: 28px 24px;
  }

  .page-title {
    flex-direction: column;
    gap: 16px;
  }
}

@media (max-width: 734px) {
  .content-list {
    padding: 20px 16px;
  }

  .page-title h2 {
    font-size: 22px;
  }

  .section-card {
    padding: 16px;
  }

  .filters {
    flex-direction: column;
  }

  .filters :deep(.el-input),
  .filters :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
