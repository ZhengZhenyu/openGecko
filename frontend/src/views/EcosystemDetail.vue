<template>
  <div class="ecosystem-detail">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.push('/ecosystem')">
          <el-icon><ArrowLeft /></el-icon> 返回列表
        </el-button>
        <div class="title-row">
          <h1 class="page-title">{{ project?.name ?? '加载中…' }}</h1>
          <el-tag v-if="project" size="small" :type="project.platform === 'github' ? 'success' : 'info'">
            {{ project.platform }}
          </el-tag>
          <el-tag v-if="project && !project.is_active" size="small" type="danger">已停用</el-tag>
        </div>
        <p v-if="project" class="project-repo">
          {{ project.org_name }}{{ project.repo_name ? `/${project.repo_name}` : '' }}
        </p>
      </div>
      <el-button type="primary" :loading="syncing" @click="handleSync">
        <el-icon><Refresh /></el-icon>
        立即同步
      </el-button>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="detail-tabs">
      <!-- ── 贡献者排行 ── -->
      <el-tab-pane label="贡献者排行" name="contributors">
        <div class="contributors-toolbar">
          <el-input
            v-model="searchQ"
            placeholder="搜索 GitHub 账号 / 昵称"
            clearable
            style="width: 240px"
            @input="debouncedSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-checkbox v-model="filterUnlinked" @change="loadContributors">仅显示未关联人脉</el-checkbox>
          <span class="total-hint">共 {{ contributorTotal }} 位贡献者</span>
        </div>

        <el-table
          v-loading="contribLoading"
          :data="contributors"
          stripe
          style="width: 100%; margin-top: 12px"
        >
          <el-table-column label="排名" width="60" align="center">
            <template #default="{ $index }">
              <span class="rank-num">{{ (contribPage - 1) * contribPageSize + $index + 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="贡献者" min-width="180">
            <template #default="{ row }">
              <div class="contributor-cell">
                <img v-if="row.avatar_url" :src="row.avatar_url" class="avatar" />
                <div v-else class="avatar-placeholder">{{ (row.github_handle || '?')[0].toUpperCase() }}</div>
                <div>
                  <div class="handle">{{ row.display_name || row.github_handle }}</div>
                  <div class="sub-handle">@{{ row.github_handle }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="近 90d 提交" prop="commit_count_90d" width="120" align="right">
            <template #default="{ row }">
              <span class="metric-val">{{ row.commit_count_90d ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="人脉关联" width="140" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.person_id" type="success" size="small">已关联</el-tag>
              <el-button
                v-else
                size="small"
                type="primary"
                plain
                :loading="importingHandle === row.github_handle"
                @click.stop="handleImport(row)"
              >
                导入人脉
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="contribPage"
            v-model:page-size="contribPageSize"
            :total="contributorTotal"
            layout="prev, pager, next, sizes"
            :page-sizes="[20, 50, 100]"
            @change="loadContributors"
          />
        </div>
      </el-tab-pane>

      <!-- ── 项目信息 ── -->
      <el-tab-pane label="项目信息" name="info">
        <div v-if="project" class="info-grid">
          <div class="info-item">
            <span class="info-label">项目名称</span>
            <span class="info-value">{{ project.name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">平台</span>
            <span class="info-value">{{ project.platform }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">组织</span>
            <span class="info-value">{{ project.org_name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">仓库</span>
            <span class="info-value">{{ project.repo_name || '—（整个组织）' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">描述</span>
            <span class="info-value">{{ project.description || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">最近同步</span>
            <span class="info-value">{{ project.last_synced_at ? formatDate(project.last_synced_at) : '未同步' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">状态</span>
            <el-switch v-model="projectActive" @change="toggleActive" />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh, Search } from '@element-plus/icons-vue'
import {
  getProject,
  syncProject,
  listContributors,
  updateProject,
  importContributorToPeople,
  type EcosystemProject,
  type EcosystemContributor,
} from '../api/ecosystem'

const route = useRoute()
const pid = Number(route.params.id)

const activeTab = ref('contributors')
const project = ref<EcosystemProject | null>(null)
const syncing = ref(false)
const projectActive = ref(true)

// Contributors
const contributors = ref<EcosystemContributor[]>([])
const contributorTotal = ref(0)
const contribLoading = ref(false)
const contribPage = ref(1)
const contribPageSize = ref(20)
const searchQ = ref('')
const filterUnlinked = ref(false)
const importingHandle = ref<string | null>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    contribPage.value = 1
    loadContributors()
  }, 300)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadProject() {
  try {
    project.value = await getProject(pid)
    projectActive.value = project.value?.is_active ?? true
  } catch {
    ElMessage.error('项目信息加载失败')
  }
}

async function loadContributors() {
  contribLoading.value = true
  try {
    const result = await listContributors(pid, {
      q: searchQ.value || undefined,
      unlinked: filterUnlinked.value || undefined,
      page: contribPage.value,
      page_size: contribPageSize.value,
    })
    contributors.value = result.items
    contributorTotal.value = result.total
  } catch {
    ElMessage.error('贡献者列表加载失败')
  } finally {
    contribLoading.value = false
  }
}

async function handleSync() {
  syncing.value = true
  try {
    const result = await syncProject(pid)
    ElMessage.success(`同步完成 — 新增 ${result.created}，更新 ${result.updated}，错误 ${result.errors}`)
    await loadProject()
    await loadContributors()
  } catch {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

async function toggleActive(val: boolean) {
  try {
    await updateProject(pid, { is_active: val })
    ElMessage.success(val ? '项目已启用' : '项目已停用')
  } catch {
    projectActive.value = !val
    ElMessage.error('状态更新失败')
  }
}

async function handleImport(contributor: EcosystemContributor) {
  importingHandle.value = contributor.github_handle
  try {
    const res = await importContributorToPeople(pid, contributor.github_handle)
    const msg = res.action === 'created' ? '已创建人脉档案并关联' : '已关联到已有人脉档案'
    ElMessage.success(msg)
    // Update local record
    contributor.person_id = res.person_id
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importingHandle.value = null
  }
}

onMounted(async () => {
  await loadProject()
  await loadContributors()
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<style scoped>
.ecosystem-detail {
  padding: 28px 32px;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.project-repo {
  font-size: 13px;
  color: #64748b;
  font-family: monospace;
  margin: 0;
}

.detail-tabs {
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 0 20px 20px;
}

.contributors-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 16px;
  flex-wrap: wrap;
}

.total-hint {
  font-size: 13px;
  color: #64748b;
  margin-left: auto;
}

.contributor-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  flex-shrink: 0;
}

.handle {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.sub-handle {
  font-size: 12px;
  color: #94a3b8;
}

.rank-num {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
}

.metric-val {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* Info tab */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 16px;
  max-width: 600px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.info-label {
  font-size: 13px;
  color: #64748b;
  min-width: 80px;
  padding-top: 2px;
}

.info-value {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
}
</style>
