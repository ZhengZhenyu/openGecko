<template>
  <div class="profile-root">
    <!-- 页面标题 -->
    <div class="page-title-row">
      <div>
        <h2>个人设置</h2>
        <p class="subtitle">管理您的账户信息与安全凭据</p>
      </div>
    </div>

    <div class="profile-grid">
      <!-- 左侧：基本信息 -->
      <div class="section-card">
        <div class="section-header">
          <h3>基本信息</h3>
        </div>

        <!-- 头像占位 -->
        <div class="avatar-area">
          <div class="avatar-circle">{{ avatarLetter }}</div>
          <div class="avatar-meta">
            <div class="username-text">{{ user?.username }}</div>
            <div class="role-badge" :class="isSuperuser ? 'badge-danger' : 'badge-blue'">
              {{ isSuperuser ? '超级管理员' : '普通用户' }}
            </div>
          </div>
        </div>

        <el-form
          ref="infoFormRef"
          :model="infoForm"
          :rules="infoRules"
          label-position="top"
          class="profile-form"
        >
          <el-form-item label="显示名称" prop="full_name">
            <el-input v-model="infoForm.full_name" placeholder="请输入显示名称" />
          </el-form-item>
          <el-form-item label="邮箱地址" prop="email">
            <el-input v-model="infoForm.email" placeholder="请输入邮箱地址" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input :model-value="user?.username" disabled>
              <template #suffix>
                <span class="field-hint">用户名不可修改</span>
              </template>
            </el-input>
          </el-form-item>

          <el-button
            type="primary"
            :loading="savingInfo"
            @click="saveInfo"
            class="save-btn"
          >
            保存基本信息
          </el-button>
        </el-form>
      </div>

      <!-- 右侧：修改密码 -->
      <div class="section-card">
        <div class="section-header">
          <h3>修改密码</h3>
        </div>

        <div class="security-tip">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          <span>修改密码后，当前登录状态将保持有效，但其他设备需要重新登录。</span>
        </div>

        <el-form
          ref="pwdFormRef"
          :model="pwdForm"
          :rules="pwdRules"
          label-position="top"
          class="profile-form"
        >
          <el-form-item label="当前密码" prop="current_password">
            <el-input
              v-model="pwdForm.current_password"
              type="password"
              show-password
              placeholder="请输入当前密码"
            />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="pwdForm.new_password"
              type="password"
              show-password
              placeholder="至少 6 位"
            />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input
              v-model="pwdForm.confirm_password"
              type="password"
              show-password
              placeholder="再次输入新密码"
            />
          </el-form-item>

          <el-button
            type="primary"
            :loading="savingPwd"
            @click="savePassword"
            class="save-btn"
          >
            更新密码
          </el-button>
        </el-form>
      </div>
    </div>

    <!-- 账号信息卡片 -->
    <div class="section-card meta-card">
      <div class="section-header">
        <h3>账号信息</h3>
      </div>
      <div class="meta-grid">
        <div class="meta-item">
          <span class="meta-label">账号创建时间</span>
          <span class="meta-value">{{ formatDate(user?.created_at) }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">账号状态</span>
          <span class="meta-value">
            <span class="role-badge badge-green">正常使用中</span>
          </span>
        </div>
        <div class="meta-item">
          <span class="meta-label">所属社区数</span>
          <span class="meta-value">{{ authStore.communities.length }} 个</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">账号类型</span>
          <span class="meta-value">{{ isSuperuser ? '超级管理员' : '社区成员' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { updateMyProfile, getUserInfo } from '../api/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const isSuperuser = computed(() => authStore.isSuperuser)

const avatarLetter = computed(() => {
  const name = user.value?.full_name || user.value?.username || '?'
  return name.charAt(0).toUpperCase()
})

// ---- 基本信息表单 ----
const infoFormRef = ref<FormInstance>()
const savingInfo = ref(false)
const infoForm = ref({
  full_name: '',
  email: '',
})

const infoRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱格式', trigger: 'blur' },
  ],
}

onMounted(() => {
  infoForm.value.full_name = user.value?.full_name || ''
  infoForm.value.email = user.value?.email || ''
})

async function saveInfo() {
  if (!infoFormRef.value) return
  await infoFormRef.value.validate(async (valid) => {
    if (!valid) return
    savingInfo.value = true
    try {
      const updated = await updateMyProfile({
        full_name: infoForm.value.full_name,
        email: infoForm.value.email,
      })
      // 更新 store 中的用户信息
      authStore.setUser(updated)
      ElMessage.success('基本信息已保存')
    } catch (err: any) {
      ElMessage.error(err?.response?.data?.detail || '保存失败，请重试')
    } finally {
      savingInfo.value = false
    }
  })
}

// ---- 修改密码表单 ----
const pwdFormRef = ref<FormInstance>()
const savingPwd = ref(false)
const pwdForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const pwdRules: FormRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== pwdForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function savePassword() {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    savingPwd.value = true
    try {
      await updateMyProfile({
        current_password: pwdForm.value.current_password,
        new_password: pwdForm.value.new_password,
      })
      ElMessage.success('密码已更新')
      pwdFormRef.value!.resetFields()
    } catch (err: any) {
      ElMessage.error(err?.response?.data?.detail || '密码更新失败，请检查当前密码是否正确')
    } finally {
      savingPwd.value = false
    }
  })
}

function formatDate(dateStr?: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<style scoped>
.profile-root {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --red:            #ef4444;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ---- 页面标题 ---- */
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
.subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

/* ---- 卡片网格 ---- */
.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

/* ---- Section card ---- */
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}
.section-card:hover {
  box-shadow: var(--shadow-hover);
}
.section-header {
  margin-bottom: 20px;
}
.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ---- 头像区域 ---- */
.avatar-area {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
}
.avatar-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0095ff, #60c3ff);
  color: #ffffff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.username-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

/* ---- Badges ---- */
.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.badge-blue   { background: #eff6ff; color: #1d4ed8; }
.badge-danger { background: #fef2f2; color: #dc2626; }
.badge-green  { background: #f0fdf4; color: #15803d; }
.badge-gray   { background: #f1f5f9; color: #64748b; }

/* ---- 表单 ---- */
.profile-form {
  margin-top: 4px;
}

:deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding-bottom: 4px;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
:deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f8fafc;
}

.field-hint {
  font-size: 11px;
  color: var(--text-muted);
}

.save-btn {
  margin-top: 4px;
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
  transition: all 0.15s ease;
}
:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

/* ---- Security tip ---- */
.security-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: #eff6ff;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #1d4ed8;
  line-height: 1.5;
}
.tip-icon {
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ---- 账号信息网格 ---- */
.meta-card {
  margin-bottom: 0;
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.meta-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.meta-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

/* ---- Responsive ---- */
@media (max-width: 1200px) {
  .profile-root { padding: 28px 24px; }
  .meta-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 734px) {
  .profile-root { padding: 20px 16px; }
  .profile-grid { grid-template-columns: 1fr; }
  .page-title-row h2 { font-size: 22px; }
  .meta-grid { grid-template-columns: 1fr 1fr; }
}
</style>
