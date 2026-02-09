<template>
  <div class="setup-container">
    <el-card class="setup-card">
      <template #header>
        <div class="card-header">
          <h2>OmniContent</h2>
          <p class="subtitle">系统初始化设置</p>
        </div>
      </template>

      <el-alert
        type="warning"
        :closable="false"
        show-icon
        class="setup-alert"
      >
        <template #title>
          欢迎使用 OmniContent！请创建您的管理员账号。
        </template>
        <p>默认管理员账号将在新账号创建后自动删除。新管理员必须配置邮箱以支持密码找回功能。</p>
      </el-alert>

      <el-form
        ref="setupFormRef"
        :model="setupForm"
        :rules="setupRules"
        label-width="100px"
        class="setup-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="setupForm.username"
            placeholder="请输入管理员用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="setupForm.email"
            placeholder="请输入邮箱地址（用于密码找回）"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item label="姓名" prop="full_name">
          <el-input
            v-model="setupForm.full_name"
            placeholder="请输入真实姓名（可选）"
            size="large"
            :prefix-icon="UserFilled"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="setupForm.password"
            type="password"
            placeholder="请设置密码（至少6位）"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="setupForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleSetup"
          />
        </el-form-item>

        <el-form-item>
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
import { useCommunityStore } from '../stores/community'

const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

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
    // Call the initial setup endpoint
    const response = await initialSetup({
      username: setupForm.username,
      email: setupForm.email,
      password: setupForm.password,
      full_name: setupForm.full_name || undefined,
    })

    // Set the new token
    authStore.setToken(response.access_token)

    // Fetch new admin user info
    const userInfo = await getUserInfo()
    // Backend returns user data directly with communities array
    const { communities, ...userData } = userInfo
    authStore.setUser(userData as any)
    authStore.setCommunities(communities)

    // Set default community if available
    if (communities.length > 0) {
      communityStore.setCommunity(communities[0].id)
    }

    ElMessage.success('管理员账号创建成功！默认账号已自动删除。')

    // Redirect to dashboard
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
.setup-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.setup-card {
  width: 520px;
  max-width: 95%;

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

  h2 {
    margin: 0 0 8px;
    font-size: 28px;
    font-weight: 600;
    color: #303133;
  }

  .subtitle {
    margin: 0;
    font-size: 14px;
    color: #e6a23c;
    font-weight: 500;
  }
}

.setup-alert {
  margin-bottom: 24px;

  p {
    margin: 8px 0 0;
    font-size: 13px;
    line-height: 1.6;
  }
}

.setup-form {
  margin-top: 20px;

  .el-form-item {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .setup-button {
    width: 100%;
    margin-top: 12px;
  }
}
</style>
