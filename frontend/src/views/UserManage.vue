<template>
  <div class="user-manage">
    <!-- 页面标题 -->
    <div class="page-title-row">
      <div class="page-title">
        <h2>用户管理</h2>
        <p class="subtitle">管理系统中的所有用户账号</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showRegisterDialog">注册新用户</el-button>
    </div>

    <!-- 用户表格 -->
    <div class="section-card">
      <div class="section-header">
        <h3>用户列表</h3>
        <span class="section-desc">共 {{ users.length }} 个用户</span>
      </div>
      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-avatar">{{ (row.full_name || row.username).charAt(0).toUpperCase() }}</div>
              <div class="user-detail">
                <span class="user-name">{{ row.full_name || row.username }}</span>
                <span class="user-email">{{ row.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <span class="role-badge" :class="row.is_superuser ? 'role-admin' : 'role-user'">
              {{ row.is_superuser ? '超级管理员' : '普通用户' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status-badge" :class="row.is_active ? 'status-active' : 'status-disabled'">
              {{ row.is_active ? '活跃' : '已禁用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            <span class="meta-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button
              v-if="row.id !== currentUser?.id"
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Register User Dialog -->
    <el-dialog v-model="registerDialogVisible" title="注册新用户" width="480px">
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="registerForm.full_name" placeholder="姓名（可选）" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            show-password
            placeholder="密码（至少6位）"
          />
        </el-form-item>
        <el-form-item label="用户类型">
          <el-checkbox v-model="registerForm.is_superuser">
            创建为超级管理员
          </el-checkbox>
          <div class="form-hint">超级管理员可以管理所有社区和用户</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRegister" :loading="submitting">注册</el-button>
      </template>
    </el-dialog>

    <!-- Edit User Dialog -->
    <el-dialog v-model="editDialogVisible" title="编辑用户" width="480px">
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="80px"
      >
        <el-form-item label="用户名">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.full_name" placeholder="姓名（可选）" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="editForm.is_active"
            active-text="活跃"
            inactive-text="禁用"
            :disabled="editForm.id === currentUser?.id"
          />
        </el-form-item>
        <el-form-item label="用户类型">
          <el-checkbox v-model="editForm.is_superuser">
            超级管理员
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listAllUsers, register, updateUser, deleteUser } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import type { User } from '../stores/auth'

const authStore = useAuthStore()
const currentUser = authStore.user

const users = ref<User[]>([])
const loading = ref(false)
const registerDialogVisible = ref(false)
const editDialogVisible = ref(false)
const submitting = ref(false)
const registerFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

const registerForm = ref({
  username: '',
  email: '',
  full_name: '',
  password: '',
  is_superuser: false,
})

const editForm = ref({
  id: 0,
  username: '',
  email: '',
  full_name: '',
  is_active: true,
  is_superuser: false,
})

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

const editRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
}

async function loadUsers() {
  loading.value = true
  try {
    users.value = await listAllUsers()
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function showRegisterDialog() {
  registerForm.value = { username: '', email: '', full_name: '', password: '', is_superuser: false }
  registerDialogVisible.value = true
}

function showEditDialog(user: User) {
  editForm.value = {
    id: user.id,
    username: user.username,
    email: user.email,
    full_name: user.full_name || '',
    is_active: user.is_active,
    is_superuser: user.is_superuser,
  }
  editDialogVisible.value = true
}

async function handleRegister() {
  if (!registerFormRef.value) return
  try {
    await registerFormRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    await register({
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password,
      full_name: registerForm.value.full_name || undefined,
      is_superuser: registerForm.value.is_superuser,
    })
    ElMessage.success('用户注册成功')
    registerDialogVisible.value = false
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '注册失败')
  } finally {
    submitting.value = false
  }
}

async function handleEdit() {
  if (!editFormRef.value) return
  try {
    await editFormRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    await updateUser(editForm.value.id, {
      email: editForm.value.email,
      full_name: editForm.value.full_name || undefined,
      is_active: editForm.value.is_active,
      is_superuser: editForm.value.is_superuser,
    })
    ElMessage.success('用户信息已更新')
    editDialogVisible.value = false
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(user: User) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${user.username}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }

  try {
    await deleteUser(user.id)
    ElMessage.success('用户已删除')
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(loadUsers)
</script>

<style scoped>
.user-manage {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --red: #ef4444;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page Title Row */
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}

.page-title {
  display: flex;
  flex-direction: column;
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

/* Section Card */
.section-card {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}

.section-card:hover {
  box-shadow: var(--shadow-hover);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-desc {
  font-size: 14px;
  color: var(--text-muted);
}

/* User Cell */
.user-cell {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--blue), #0080e6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-email {
  font-size: 13px;
  color: var(--text-muted);
}

/* Role Badge */
.role-badge {
  display: inline-block;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.role-admin {
  background: #fef2f2;
  color: #ef4444;
}

.role-user {
  background: #f1f5f9;
  color: #64748b;
}

/* Status Badge */
.status-badge {
  display: inline-block;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.status-active {
  background: #f0fdf4;
  color: #15803d;
}

.status-disabled {
  background: #fef2f2;
  color: var(--red);
}

/* Meta Text */
.meta-text {
  font-size: 13px;
  color: var(--text-muted);
}

/* Element Plus table overrides */
:deep(.el-table) {
  background: transparent;
  color: var(--text-primary);
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
  padding: 14px 0;
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #f1f5f9;
  padding: 14px 0;
  font-size: 14px;
  color: var(--text-primary);
}

:deep(.el-table tbody tr:hover > td) {
  background: #f8fafc !important;
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
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

:deep(.el-button--text) {
  color: var(--blue);
}

:deep(.el-button--text:hover) {
  color: #0080e6;
  background: rgba(0, 149, 255, 0.08);
}

:deep(.el-empty) {
  color: var(--text-secondary);
}

:deep(.el-empty__description) {
  color: var(--text-muted);
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
