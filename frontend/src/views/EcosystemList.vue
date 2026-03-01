<template>
  <div class="ecosystem-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">生态洞察</h1>
        <p class="page-subtitle">监控开源生态项目，追踪贡献者动态</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        添加项目
      </el-button>
    </div>

    <!-- Project Grid -->
    <div v-loading="loading" class="project-grid">
      <div v-if="!loading && projects.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Connection /></el-icon>
        <p>暂无生态项目，点击右上角添加</p>
      </div>

      <div
        v-for="p in projects"
        :key="p.id"
        class="project-card"
        @click="$router.push(`/ecosystem/${p.id}`)"
      >
        <div class="card-top">
          <el-tag size="small" :type="p.platform === 'github' ? 'success' : 'info'">
            {{ p.platform }}
          </el-tag>
          <el-tag v-if="!p.is_active" size="small" type="danger">已停用</el-tag>
        </div>
        <h3 class="project-name">{{ p.name }}</h3>
        <p class="project-repo">{{ p.org_name }}{{ p.repo_name ? `/${p.repo_name}` : '' }}</p>
        <p v-if="p.description" class="project-desc">{{ p.description }}</p>
        <div class="card-footer">
          <span v-if="p.last_synced_at" class="sync-time">
            <el-icon><Refresh /></el-icon>
            {{ formatDate(p.last_synced_at) }}
          </span>
          <span v-else class="sync-time muted">未同步</span>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="添加生态项目" width="480px" destroy-on-close>
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="项目名称" required>
          <el-input v-model="createForm.name" placeholder="如: OpenKruise" />
        </el-form-item>
        <el-form-item label="平台" required>
          <el-select v-model="createForm.platform" style="width: 100%">
            <el-option label="GitHub" value="github" />
            <el-option label="Gitee" value="gitee" />
            <el-option label="GitCode" value="gitcode" />
          </el-select>
        </el-form-item>
        <el-form-item label="组织名" required>
          <el-input v-model="createForm.org_name" placeholder="如: openkruise" />
        </el-form-item>
        <el-form-item label="仓库名">
          <el-input v-model="createForm.repo_name" placeholder="如: kruise（留空=整个组织）" />
        </el-form-item>
        <el-form-item label="关联社区">
          <el-select v-model="createForm.community_id" placeholder="可选，关联到某社区" clearable style="width: 100%">
            <el-option v-for="c in communities" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-divider style="margin: 12px 0" />
        <el-form-item label="自动采集">
          <el-switch v-model="createForm.auto_sync_enabled" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item v-if="createForm.auto_sync_enabled" label="采集间隔">
          <el-input-number
            v-model="createForm.sync_interval_hours"
            :min="1"
            :max="720"
            :placeholder="'留空=全局默认'"
            style="width: 140px"
          />
          <span style="margin-left: 8px; color: var(--text-secondary); font-size: 13px">小时（留空使用全局默认）</span>
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
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Connection, Refresh } from '@element-plus/icons-vue'
import { listProjects, createProject, type EcosystemProject, type ProjectCreateData } from '../api/ecosystem'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const communities = computed(() => authStore.communities)
const loading = ref(false)
const projects = ref<EcosystemProject[]>([])
const showCreateDialog = ref(false)
const creating = ref(false)

const createForm = ref({
  name: '',
  platform: 'github',
  org_name: '',
  repo_name: '',
  description: '',
  community_id: null as number | null,
  auto_sync_enabled: true,
  sync_interval_hours: null as number | null,
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadProjects() {
  loading.value = true
  try {
    projects.value = await listProjects()
  } catch {
    // 错误已由 API 拦截器统一展示
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createForm.value = { name: '', platform: 'github', org_name: '', repo_name: '', description: '', community_id: null, auto_sync_enabled: true, sync_interval_hours: null }
  showCreateDialog.value = true
}

async function handleCreate() {
  if (!createForm.value.name.trim() || !createForm.value.org_name.trim()) {
    ElMessage.warning('请填写项目名称和组织名')
    return
  }
  creating.value = true
  try {
    const payload: ProjectCreateData = {
      name: createForm.value.name,
      platform: createForm.value.platform,
      org_name: createForm.value.org_name,
      community_id: createForm.value.community_id || null,
      auto_sync_enabled: createForm.value.auto_sync_enabled,
      sync_interval_hours: createForm.value.sync_interval_hours || null,
    }
    if (createForm.value.repo_name) payload.repo_name = createForm.value.repo_name
    if (createForm.value.description) payload.description = createForm.value.description
    await createProject(payload)
    ElMessage.success('项目已添加')
    showCreateDialog.value = false
    await loadProjects()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    creating.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.ecosystem-page {
  padding: 28px 32px;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: #94a3b8;
  font-size: 14px;
}

.empty-icon {
  font-size: 40px;
}

.project-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px 20px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-card:hover {
  box-shadow: 0 4px 16px rgba(0, 149, 255, 0.1);
  border-color: #0095ff;
}

.card-top {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.project-repo {
  font-size: 12px;
  color: #64748b;
  font-family: monospace;
  margin: 0;
}

.project-desc {
  font-size: 13px;
  color: #475569;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.sync-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
}

.sync-time.muted {
  color: #94a3b8;
}
</style>
