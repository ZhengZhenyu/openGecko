<template>
  <div class="community-manage">
    <!-- Page Header -->
    <div class="page-title-row">
      <div class="page-title">
        <h2>社区管理</h2>
        <p class="subtitle">管理所有社区，点击卡片进入社区设置</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建社区</el-button>
    </div>

    <!-- Community Cards -->
    <div v-if="loading" class="loading-state" v-loading="loading" style="min-height: 200px;" />
    <div v-else-if="communities.length === 0" class="empty-state">
      <p>暂无社区，点击右上角创建第一个社区</p>
    </div>
    <el-row v-else :gutter="20">
      <el-col :span="8" v-for="community in communities" :key="community.id">
        <div class="community-card" @click="goToSettings(community)">
          <!-- Card Top -->
          <div class="card-top">
            <div class="community-avatar">{{ community.name.charAt(0).toUpperCase() }}</div>
            <div class="community-main">
              <div class="community-name-row">
                <span class="community-name">{{ community.name }}</span>
                <el-tag v-if="!community.is_active" type="danger" size="small">已停用</el-tag>
              </div>
              <div class="community-slug">
                <el-icon><Link /></el-icon>
                <span>{{ community.slug }}</span>
              </div>
            </div>
            <!-- More actions -->
            <el-dropdown
              @command="(cmd: string) => handleAction(cmd, community)"
              @click.stop
              trigger="click"
            >
              <el-icon class="more-icon" @click.stop><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="community.is_active ? 'disable' : 'enable'">
                    {{ community.is_active ? '停用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #ef4444;">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <!-- Card Body -->
          <p class="community-desc">{{ community.description || '暂无描述' }}</p>

          <!-- Card Footer -->
          <div class="card-footer">
            <a
              v-if="community.url"
              :href="community.url"
              target="_blank"
              rel="noopener"
              class="community-url"
              @click.stop
            >
              {{ community.url }}
            </a>
            <span v-else class="no-url">未设置官网</span>
            <span class="settings-btn">
              进入设置 <el-icon><ArrowRight /></el-icon>
            </span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Create Community Dialog -->
    <el-dialog v-model="dialogVisible" title="新建社区" width="500px">
      <el-form
        ref="formRef"
        :model="communityForm"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="communityForm.name" placeholder="社区名称" />
        </el-form-item>
        <el-form-item label="标识" prop="slug">
          <el-input
            v-model="communityForm.slug"
            placeholder="英文标识（如 my-community）"
          />
          <div class="form-hint">创建后不可修改，只能包含小写字母、数字和连字符</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="communityForm.description"
            type="textarea"
            :rows="3"
            placeholder="社区描述（可选）"
          />
        </el-form-item>
        <el-form-item label="官网">
          <el-input v-model="communityForm.url" placeholder="社区官网或项目仓库地址（可选）" />
        </el-form-item>
        <el-form-item label="Logo URL">
          <el-input v-model="communityForm.logo_url" placeholder="Logo 图片地址（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, MoreFilled, Link, ArrowRight } from '@element-plus/icons-vue'
import type { Community } from '../stores/auth'
import { useAuthStore } from '../stores/auth'
import { getCommunities, createCommunity, updateCommunity, deleteCommunity } from '../api/community'

const router = useRouter()
useAuthStore()

const communities = ref<Community[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const communityForm = ref({
  name: '',
  slug: '',
  description: '',
  url: '',
  logo_url: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入社区名称', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入社区标识', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' },
  ],
}

function goToSettings(community: Community) {
  router.push(`/community-settings/${community.id}`)
}

function showCreateDialog() {
  communityForm.value = { name: '', slug: '', description: '', url: '', logo_url: '' }
  dialogVisible.value = true
}

async function handleCreate() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    await createCommunity(communityForm.value)
    ElMessage.success('社区创建成功')
    dialogVisible.value = false
    await loadCommunities()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

async function handleAction(command: string, community: Community) {
  if (command === 'enable' || command === 'disable') {
    try {
      await updateCommunity(community.id, { is_active: !community.is_active })
      ElMessage.success(community.is_active ? '社区已停用' : '社区已启用')
      await loadCommunities()
    } catch {
      ElMessage.error('操作失败')
    }
  } else if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除社区「${community.name}」吗？此操作不可恢复，所有相关数据将被删除。`,
        '删除确认',
        { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
      )
      await deleteCommunity(community.id)
      ElMessage.success('社区已删除')
      await loadCommunities()
    } catch {
      // cancelled
    }
  }
}

async function loadCommunities() {
  loading.value = true
  try {
    communities.value = await getCommunities()
  } catch {
    ElMessage.error('加载社区列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadCommunities)
</script>

<style scoped>
.community-manage {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.1);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page Header */
.page-title-row {
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
  color: var(--text-secondary);
  font-size: 15px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 15px;
}

/* Community Card */
.community-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.community-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: #cbd5e1;
}

/* Card Top */
.card-top {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.community-avatar {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--blue), #0080e6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.community-main {
  flex: 1;
  min-width: 0;
}

.community-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.community-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.community-slug {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.more-icon {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 18px;
  padding: 4px;
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}

.more-icon:hover {
  color: var(--text-secondary);
  background: #f1f5f9;
}

/* Card Body */
.community-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  flex: 1;
  /* Clamp to 2 lines */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Card Footer */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #f1f5f9;
  padding-top: 12px;
  margin-top: auto;
  gap: 8px;
}

.community-url {
  font-size: 12px;
  color: var(--blue);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  transition: opacity 0.15s;
}

.community-url:hover {
  text-decoration: underline;
  opacity: 0.85;
}

.no-url {
  font-size: 12px;
  color: var(--text-muted);
  flex: 1;
}

.settings-btn {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--blue);
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.settings-btn:hover {
  opacity: 0.75;
}

/* Form hint */
.form-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Element Plus overrides */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-dialog) {
  border-radius: var(--radius);
}
</style>
