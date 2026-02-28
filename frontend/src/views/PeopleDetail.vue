<template>
  <div class="people-detail">
    <!-- Back + Header -->
    <div class="detail-header">
      <el-button link @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>返回人脉列表
      </el-button>
    </div>

    <div v-if="loading" class="loading-wrap" v-loading="loading" style="min-height: 300px;" />

    <template v-else-if="person">
      <!-- Profile Card -->
      <div class="profile-card section-card">
        <div class="profile-top">
          <el-avatar :size="64" :src="person.avatar_url ?? ''" class="profile-avatar">
            {{ person.display_name.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="profile-info">
            <div class="profile-name-row">
              <h2 class="profile-name">{{ person.display_name }}</h2>
              <span v-for="tag in person.tags" :key="tag" class="tag-badge">{{ tag }}</span>
            </div>
            <div class="profile-meta">
              <span v-if="person.company"><el-icon><OfficeBuilding /></el-icon>{{ person.company }}</span>
              <span v-if="person.location"><el-icon><Location /></el-icon>{{ person.location }}</span>
              <span v-if="person.email"><el-icon><Message /></el-icon>{{ person.email }}</span>
              <a v-if="person.github_handle" :href="`https://github.com/${person.github_handle}`" target="_blank" class="github-link">
                <el-icon><Link /></el-icon>@{{ person.github_handle }}
              </a>
            </div>
            <p v-if="person.bio" class="profile-bio">{{ person.bio }}</p>
          </div>
          <div class="profile-actions">
            <el-button @click="openEditDialog">编辑</el-button>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="section-card tabs-card">
        <el-tabs v-model="activeTab">
          <!-- Roles Timeline Tab -->
          <el-tab-pane label="社区角色" name="roles">
            <div class="tab-content">
              <div class="tab-actions">
                <el-button size="small" type="primary" @click="openAddRoleDialog">
                  <el-icon><Plus /></el-icon>添加角色
                </el-button>
              </div>
              <div v-if="roles.length === 0" class="tab-empty">暂无角色记录</div>
              <div v-for="role in rolesSorted" :key="role.id" class="role-item">
                <div class="role-dot" :class="role.is_current ? 'dot-active' : 'dot-past'" />
                <div class="role-body">
                  <div class="role-top-row">
                    <span class="role-community">{{ role.community_name }}</span>
                    <span class="role-name">{{ role.role_label || role.role }}</span>
                    <el-tag v-if="role.is_current" type="success" size="small">当前</el-tag>
                  </div>
                  <div class="role-dates">
                    {{ role.started_at ?? '?' }} ~ {{ role.is_current ? '至今' : (role.ended_at ?? '?') }}
                  </div>
                  <a v-if="role.source_url" :href="role.source_url" target="_blank" class="role-link">查看来源</a>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Basic Info Tab -->
          <el-tab-pane label="详细信息" name="info">
            <div class="tab-content info-grid">
              <div class="info-row"><span class="info-label">来源</span><span>{{ sourceLabel[person.source] ?? person.source }}</span></div>
              <div class="info-row"><span class="info-label">手机</span><span>{{ person.phone ?? '-' }}</span></div>
              <div class="info-row"><span class="info-label">GitCode</span><span>{{ person.gitcode_handle ?? '-' }}</span></div>
              <div class="info-row"><span class="info-label">备注</span><span class="notes-text">{{ person.notes ?? '-' }}</span></div>
              <div class="info-row"><span class="info-label">创建时间</span><span>{{ formatDateTime(person.created_at) }}</span></div>
              <div class="info-row"><span class="info-label">更新时间</span><span>{{ formatDateTime(person.updated_at) }}</span></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>

    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑人脉档案" width="520px" destroy-on-close>
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="姓名" required>
          <el-input v-model="editForm.display_name" />
        </el-form-item>
        <el-form-item label="GitHub">
          <el-input v-model="editForm.github_handle" placeholder="GitHub 用户名" />
        </el-form-item>
        <el-form-item label="GitCode">
          <el-input v-model="editForm.gitcode_handle" placeholder="GitCode 用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="公司 / 组织">
          <el-input v-model="editForm.company" />
        </el-form-item>
        <el-form-item label="所在地">
          <el-input v-model="editForm.location" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="editForm.bio" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="editForm.tags"
            multiple filterable allow-create default-first-option
            style="width:100%" placeholder="输入后回车添加标签"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Add Role Dialog -->
    <el-dialog v-model="showAddRoleDialog" title="添加社区角色" width="480px" destroy-on-close>
      <el-form :model="roleForm" label-width="90px">
        <el-form-item label="社区名称" required>
          <el-input v-model="roleForm.community_name" placeholder="如：openEuler" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="roleForm.role" style="width:100%">
            <el-option label="Maintainer" value="maintainer" />
            <el-option label="Committer" value="committer" />
            <el-option label="Contributor" value="contributor" />
            <el-option label="TC 成员" value="tc_member" />
            <el-option label="委员会成员" value="committee_member" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色备注">
          <el-input v-model="roleForm.role_label" placeholder="可选，如：安全委员会主席" />
        </el-form-item>
        <el-form-item label="项目链接">
          <el-input v-model="roleForm.project_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="roleForm.started_at" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="roleForm.ended_at" type="date" value-format="YYYY-MM-DD" style="width:100%" :disabled="roleForm.is_current" />
        </el-form-item>
        <el-form-item label="当前在任">
          <el-switch v-model="roleForm.is_current" />
        </el-form-item>
        <el-form-item label="来源链接">
          <el-input v-model="roleForm.source_url" placeholder="https://..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRoleDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingRole" @click="handleAddRole">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, OfficeBuilding, Location, Message, Link } from '@element-plus/icons-vue'
import { getPerson, updatePerson, listPersonRoles, addPersonRole } from '../api/people'
import type { PersonOut, CommunityRoleOut } from '../api/people'

const route = useRoute()
const router = useRouter()
const personId = computed(() => Number(route.params.id))

// ─── State ────────────────────────────────────────────────────────────────────
const loading = ref(false)
const person = ref<PersonOut | null>(null)
const roles = ref<CommunityRoleOut[]>([])
const activeTab = ref('roles')

const showEditDialog = ref(false)
const saving = ref(false)
const editForm = ref({
  display_name: '',
  github_handle: '',
  gitcode_handle: '',
  email: '',
  phone: '',
  company: '',
  location: '',
  bio: '',
  tags: [] as string[],
  notes: '',
})

const showAddRoleDialog = ref(false)
const savingRole = ref(false)
const roleForm = ref({
  community_name: '',
  role: 'contributor',
  role_label: '',
  project_url: '',
  started_at: null as string | null,
  ended_at: null as string | null,
  is_current: true,
  source_url: '',
})

// ─── Labels ───────────────────────────────────────────────────────────────────
const sourceLabel: Record<string, string> = {
  manual: '手动录入',
  event_import: '活动导入',
  github: 'GitHub',
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const rolesSorted = computed(() =>
  [...roles.value].sort((a, b) => {
    if (a.is_current !== b.is_current) return a.is_current ? -1 : 1
    const da = a.started_at ?? ''
    const db = b.started_at ?? ''
    return db.localeCompare(da)
  })
)

// ─── Load ─────────────────────────────────────────────────────────────────────
async function loadPerson() {
  loading.value = true
  try {
    const [p, r] = await Promise.all([
      getPerson(personId.value),
      listPersonRoles(personId.value),
    ])
    person.value = p
    roles.value = r
  } catch {
    ElMessage.error('加载人脉档案失败')
    router.push('/people')
  } finally {
    loading.value = false
  }
}

// ─── Edit ─────────────────────────────────────────────────────────────────────
function openEditDialog() {
  if (!person.value) return
  const p = person.value
  editForm.value = {
    display_name: p.display_name,
    github_handle: p.github_handle ?? '',
    gitcode_handle: p.gitcode_handle ?? '',
    email: p.email ?? '',
    phone: p.phone ?? '',
    company: p.company ?? '',
    location: p.location ?? '',
    bio: p.bio ?? '',
    tags: [...p.tags],
    notes: p.notes ?? '',
  }
  showEditDialog.value = true
}

async function handleSaveEdit() {
  if (!editForm.value.display_name.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }
  saving.value = true
  try {
    person.value = await updatePerson(personId.value, {
      display_name: editForm.value.display_name,
      github_handle: editForm.value.github_handle || null,
      gitcode_handle: editForm.value.gitcode_handle || null,
      email: editForm.value.email || null,
      phone: editForm.value.phone || null,
      company: editForm.value.company || null,
      location: editForm.value.location || null,
      bio: editForm.value.bio || null,
      tags: editForm.value.tags,
      notes: editForm.value.notes || null,
    })
    showEditDialog.value = false
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// ─── Add Role ─────────────────────────────────────────────────────────────────
function openAddRoleDialog() {
  roleForm.value = {
    community_name: '',
    role: 'contributor',
    role_label: '',
    project_url: '',
    started_at: null,
    ended_at: null,
    is_current: true,
    source_url: '',
  }
  showAddRoleDialog.value = true
}

async function handleAddRole() {
  if (!roleForm.value.community_name.trim()) {
    ElMessage.warning('请输入社区名称')
    return
  }
  savingRole.value = true
  try {
    const newRole = await addPersonRole(personId.value, {
      community_name: roleForm.value.community_name,
      role: roleForm.value.role,
      role_label: roleForm.value.role_label || null,
      project_url: roleForm.value.project_url || null,
      started_at: roleForm.value.started_at || null,
      ended_at: roleForm.value.is_current ? null : (roleForm.value.ended_at || null),
      is_current: roleForm.value.is_current,
      source_url: roleForm.value.source_url || null,
    })
    roles.value.push(newRole)
    showAddRoleDialog.value = false
    ElMessage.success('角色已添加')
  } catch {
    ElMessage.error('添加失败')
  } finally {
    savingRole.value = false
  }
}

// ─── Utils ────────────────────────────────────────────────────────────────────
function formatDateTime(dt: string): string {
  return new Date(dt).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => loadPerson())
</script>

<style scoped>
.people-detail {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;

  padding: 32px 40px 60px;
  max-width: 1000px;
  margin: 0 auto;
}

.detail-header {
  margin-bottom: 20px;
}

.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
}

/* Profile Card */
.profile-top {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.profile-avatar {
  flex-shrink: 0;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 22px;
  font-weight: 700;
}
.profile-info {
  flex: 1;
  min-width: 0;
}
.profile-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.profile-name {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
.tag-badge {
  display: inline-block;
  font-size: 11px;
  border-radius: 6px;
  padding: 2px 8px;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 500;
}
.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.profile-meta span,
.profile-meta a {
  display: flex;
  align-items: center;
  gap: 4px;
}
.github-link {
  color: var(--blue);
  text-decoration: none;
}
.github-link:hover { text-decoration: underline; }
.profile-bio {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.profile-actions {
  flex-shrink: 0;
}

/* Tabs */
.tabs-card {
  padding: 0 24px 20px;
}
.tab-content {
  padding: 16px 0;
}
.tab-actions {
  margin-bottom: 16px;
}
.tab-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 32px 0;
  font-size: 14px;
}

/* Roles Timeline */
.role-item {
  display: flex;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}
.role-item:last-child { border-bottom: none; }
.role-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.dot-active { background: #22c55e; }
.dot-past   { background: #cbd5e1; }
.role-body { flex: 1; }
.role-top-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.role-community {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.role-name {
  font-size: 13px;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 4px;
  padding: 1px 6px;
}
.role-dates {
  font-size: 12px;
  color: var(--text-muted);
}
.role-link {
  font-size: 12px;
  color: var(--blue);
  text-decoration: none;
}
.role-link:hover { text-decoration: underline; }

/* Info Grid */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.info-row {
  display: flex;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 14px;
}
.info-row:last-child { border-bottom: none; }
.info-label {
  width: 90px;
  flex-shrink: 0;
  font-weight: 500;
  color: var(--text-muted);
  font-size: 13px;
}
.notes-text {
  white-space: pre-wrap;
  color: var(--text-secondary);
}

/* Buttons / Inputs */
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
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}
:deep(.el-button--default:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
:deep(.el-dialog) { border-radius: var(--radius); }
:deep(.el-dialog__header) { border-bottom: 1px solid #f1f5f9; }

@media (max-width: 734px) {
  .people-detail { padding: 20px 16px; }
  .profile-top { flex-direction: column; }
  .section-card { padding: 16px; }
}
</style>