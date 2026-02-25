<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <img src="/openGecko-vertical.png" alt="openGecko" class="logo" />
          <h2>openGecko</h2>
          <p class="subtitle">多社区运营管理平台<br/>Manage All, Publish Everywhere</p>
        </div>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="0"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-links">
        <router-link to="/forgot-password" class="forgot-link">忘记密码？</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login, getUserInfo } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'

const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    // Step 1: Login and get token
    const loginResponse = await login(loginForm)
    authStore.setToken(loginResponse.access_token)

    // Check if this is the default admin - redirect to initial setup
    if (loginResponse.is_default_admin) {
      console.log('[Login] Default admin detected, redirecting to initial setup...')
      // Redirect to initial setup immediately without showing message
      // The InitialSetup page will show appropriate instructions
      router.push('/initial-setup')
      return
    }

    // Step 2: Fetch user info and communities
    const userInfo = await getUserInfo()
    authStore.setUser(userInfo.user)
    authStore.setCommunities(userInfo.communities)

    // Step 3: Set community if available
    if (userInfo.communities.length > 0) {
      communityStore.setCommunity(userInfo.communities[0].id)
      ElMessage.success('登录成功')
    } else {
      ElMessage.success('登录成功，请先创建或加入社区')
    }

    // Step 4: Redirect to dashboard
    router.push('/')
  } catch (error: any) {
    console.error('Login failed:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
/* LFX Insights Light Theme - Login */
.login-container {
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

.login-card {
  position: relative;
  width: 420px;
  max-width: 90%;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);

  :deep(.el-card__header) {
    padding: 28px 32px 20px;
    border-bottom: 1px solid #f1f5f9;
    background: transparent;
  }

  :deep(.el-card__body) {
    padding: 24px 32px 28px;
    background: transparent;
  }
}

.card-header {
  text-align: center;

  .logo {
    width: 160px;
    height: auto;
    margin: 0 auto 14px;
    display: block;
    border-radius: 12px;
    padding: 8px;
  }

  h2 {
    margin: 0 0 8px;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #1e293b;
  }

  .subtitle {
    margin: 0;
    font-size: 13px;
    font-weight: 400;
    line-height: 1.5;
    color: #64748b;
    letter-spacing: 0.011em;
  }
}

.login-form {
  margin-top: 20px;

  .el-form-item {
    margin-bottom: 14px;

    &:last-child {
      margin-bottom: 0;
      margin-top: 20px;
    }
  }

  :deep(.el-input) {
    .el-input__wrapper {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      box-shadow: none;
      padding: 10px 16px;
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
      font-size: 14px;
      font-weight: 400;
      letter-spacing: -0.01em;

      &::placeholder {
        color: #94a3b8;
      }
    }

    .el-input__prefix {
      color: #94a3b8;
      font-size: 16px;
    }

    .el-input__suffix {
      color: #94a3b8;
    }
  }

  .login-button {
    width: 100%;
    height: 44px;
    background: #0095ff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
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

.login-links {
  margin-top: 16px;
  text-align: right;

  .forgot-link {
    color: #64748b;
    text-decoration: none;
    font-size: 14px;
    font-weight: 400;
    letter-spacing: -0.01em;
    transition: color 0.15s ease;

    &:hover {
      color: #0095ff;
    }
  }
}

/* Responsive */
@media (max-width: 640px) {
  .login-card {
    width: calc(100% - 40px);
    margin: 20px;

    :deep(.el-card__header) {
      padding: 24px 24px 16px;
    }

    :deep(.el-card__body) {
      padding: 20px 24px 24px;
    }
  }

  .card-header {
    .logo {
      width: 130px;
      margin-bottom: 12px;
    }

    h2 {
      font-size: 20px;
    }

    .subtitle {
      font-size: 12px;
    }
  }

  .login-form {
    .login-button {
      height: 40px;
      font-size: 14px;
    }
  }
}
</style>
