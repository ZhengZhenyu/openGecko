<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <img src="/logo.svg" alt="OmniContent" class="logo" />
          <h2>OmniContent</h2>
          <p class="subtitle">企业级多社区内容管理平台</p>
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
      ElMessage.warning('请先完成系统初始化设置')
      router.push('/initial-setup')
      return
    }

    // Step 2: Fetch user info and communities
    const userInfo = await getUserInfo()
    authStore.setUser(userInfo.user)
    authStore.setCommunities(userInfo.communities)

    // Step 3: Set default community if available
    if (userInfo.communities.length > 0) {
      communityStore.setCommunity(userInfo.communities[0].id)
    }

    ElMessage.success('登录成功')

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
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  max-width: 90%;

  :deep(.el-card__header) {
    padding: 30px 20px 20px;
    border-bottom: none;
  }

  :deep(.el-card__body) {
    padding: 0 40px 40px;
  }
}

.card-header {
  text-align: center;

  .logo {
    width: 80px;
    height: 80px;
    margin-bottom: 16px;
  }

  h2 {
    margin: 0 0 8px;
    font-size: 28px;
    font-weight: 600;
    color: #303133;
  }

  .subtitle {
    margin: 0;
    font-size: 14px;
    color: #909399;
  }
}

.login-form {
  margin-top: 30px;

  .el-form-item {
    margin-bottom: 24px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .login-button {
    width: 100%;
    margin-top: 12px;
  }
}

.login-links {
  margin-top: 16px;
  text-align: right;

  .forgot-link {
    color: #409eff;
    text-decoration: none;
    font-size: 13px;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
