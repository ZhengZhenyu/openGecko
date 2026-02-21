<template>
  <div class="setup-container">
    <el-card class="setup-card">
      <template #header>
        <div class="card-header">
          <img src="/openGecko-Horizontal.png" alt="openGecko" class="logo" />
          <h2>系统初始化</h2>
          <p class="subtitle">创建您的超级管理员账号以启用系统</p>
        </div>
      </template>

      <!-- Info banner -->
      <div class="info-banner">
        <svg class="info-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
        <span>创建后默认管理员账号将自动删除，请妥善保管新账号信息。</span>
      </div>

      <el-form
        ref="setupFormRef"
        :model="setupForm"
        :rules="setupRules"
        label-width="0"
        class="setup-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="setupForm.username"
            placeholder="用户名（3-100 字符）"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="setupForm.email"
            placeholder="邮箱地址（用于密码找回）"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="full_name">
          <el-input
            v-model="setupForm.full_name"
            placeholder="真实姓名（可选）"
            size="large"
            :prefix-icon="UserFilled"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="setupForm.password"
            type="password"
            placeholder="密码（至少 6 位）"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="setupForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleSetup"
          />
        </el-form-item>

        <el-form-item class="submit-item">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="setup-button"
            @click="handleSetup"
          >
            {{ loading ? '创建中...' : '创建管理员账号并启用系统' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message, UserFilled } from '@element-plus/icons-vue'
import { initialSetup, getUserInfo } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const setupFormRef = ref<FormInstance>()
const loading = ref(false)

const setupForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== setupForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const setupRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 100, message: '用户名长度为 3-100 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleSetup = async () => {
  if (!setupFormRef.value) return

  try {
    await setupFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    const response = await initialSetup({
      username: setupForm.username,
      email: setupForm.email,
      password: setupForm.password,
      full_name: setupForm.full_name || undefined,
    })

    authStore.setToken(response.access_token)

    const userInfo = await getUserInfo()
    authStore.setUser(userInfo.user)
    authStore.setCommunities(userInfo.communities)

    ElMessage.success('管理员账号创建成功！请创建社区开始使用。')
    router.push('/')
  } catch (error: any) {
    console.error('Setup failed:', error)
    ElMessage.error(error.response?.data?.detail || '初始化设置失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
/* LFX Insights Light Theme - Initial Setup */
.setup-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fa;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;

  &::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -20%;
    width: 800px;
    height: 800px;
    background: radial-gradient(circle, rgba(0, 149, 255, 0.06) 0%, transparent 70%);
    pointer-events: none;
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(34, 197, 94, 0.04) 0%, transparent 70%);
    pointer-events: none;
  }
}

.setup-card {
  position: relative;
  width: 500px;
  max-width: 90%;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);

  :deep(.el-card__header) {
    padding: 48px 40px 32px;
    border-bottom: 1px solid #f1f5f9;
    background: transparent;
  }

  :deep(.el-card__body) {
    padding: 32px 40px 40px;
    background: transparent;
  }
}

.card-header {
  text-align: center;

  .logo {
    width: 200px;
    height: auto;
    margin: 0 auto 24px;
    display: block;
    border-radius: 16px;
    padding: 12px;
  }

  h2 {
    margin: 0 0 12px;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #1e293b;
  }

  .subtitle {
    margin: 0;
    font-size: 15px;
    font-weight: 400;
    line-height: 1.5;
    color: #64748b;
    letter-spacing: 0.011em;
  }
}

.info-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 24px;
  font-size: 13px;
  color: #1d4ed8;
  line-height: 1.5;

  .info-icon {
    flex-shrink: 0;
    width: 16px;
    height: 16px;
    margin-top: 1px;
  }
}

.setup-form {
  .el-form-item {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(.el-input) {
    .el-input__wrapper {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      box-shadow: none;
      padding: 12px 16px;
      transition: all 0.2s ease;

      &:hover {
        background: #ffffff;
        border-color: #cbd5e1;
      }

      &.is-focus {
        background: #ffffff;
        border-color: #0095ff;
        box-shadow: 0 0 0 3px rgba(0, 149, 255, 0.1);
      }
    }

    .el-input__inner {
      color: #1e293b;
      font-size: 15px;
      font-weight: 400;
      letter-spacing: -0.01em;

      &::placeholder {
        color: #94a3b8;
      }
    }

    .el-input__prefix {
      color: #94a3b8;
      font-size: 17px;
    }

    .el-input__suffix {
      color: #94a3b8;
    }
  }

  .submit-item {
    margin-top: 8px;
    margin-bottom: 0;
  }

  .setup-button {
    width: 100%;
    height: 52px;
    background: #0095ff;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: -0.01em;
    box-shadow: 0 2px 8px rgba(0, 149, 255, 0.25);
    transition: all 0.2s ease;

    &:hover {
      background: #0080e6;
      box-shadow: 0 4px 12px rgba(0, 149, 255, 0.35);
    }

    &:active {
      background: #006acc;
    }
  }
}

/* Responsive */
@media (max-width: 640px) {
  .setup-card {
    width: calc(100% - 40px);
    margin: 20px;

    :deep(.el-card__header) {
      padding: 40px 28px 28px;
    }

    :deep(.el-card__body) {
      padding: 28px;
    }
  }

  .card-header {
    .logo {
      width: 160px;
      margin-bottom: 20px;
    }

    h2 {
      font-size: 24px;
    }
  }
}
</style>
