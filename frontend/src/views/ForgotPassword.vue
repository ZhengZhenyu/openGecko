<template>
  <div class="forgot-container">
    <el-card class="forgot-card">
      <template #header>
        <div class="card-header">
          <h2>openGecko</h2>
          <p class="subtitle">密码找回</p>
        </div>
      </template>

      <!-- Step 1: Enter email -->
      <div v-if="!submitted">
        <p class="description">
          请输入您注册时使用的邮箱地址，我们将向您发送密码重置链接。
        </p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          label-width="0"
          class="forgot-form"
        >
          <el-form-item prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱地址"
              size="large"
              :prefix-icon="Message"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="submit-button"
              @click="handleSubmit"
            >
              {{ loading ? '发送中...' : '发送重置链接' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 2: Success message -->
      <div v-else class="success-message">
        <el-result icon="success" title="请求已提交">
          <template #sub-title>
            <p>{{ resultMessage }}</p>
            <p v-if="devResetUrl" class="dev-url">
              <el-tag type="warning">开发模式</el-tag>
              <br>
              <a :href="devResetUrl" class="reset-link">点击此处重置密码</a>
            </p>
          </template>
          <template #extra>
            <el-button type="primary" @click="router.push('/login')">返回登录</el-button>
          </template>
        </el-result>
      </div>

      <div class="back-link">
        <router-link to="/login">
          <el-icon><ArrowLeft /></el-icon>
          返回登录
        </router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message, ArrowLeft } from '@element-plus/icons-vue'
import { requestPasswordReset } from '../api/auth'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitted = ref(false)
const resultMessage = ref('')
const devResetUrl = ref('')

const form = reactive({
  email: '',
})

const formRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    const response = await requestPasswordReset(form.email)
    resultMessage.value = response.message
    devResetUrl.value = response.reset_url || ''
    submitted.value = true
  } catch (error: any) {
    console.error('Password reset request failed:', error)
    ElMessage.error(error.response?.data?.detail || '请求失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.forgot-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.forgot-card {
  width: 440px;
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

.description {
  text-align: center;
  color: #606266;
  font-size: 14px;
  margin-bottom: 24px;
  line-height: 1.6;
}

.forgot-form {
  .el-form-item {
    margin-bottom: 24px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .submit-button {
    width: 100%;
    margin-top: 12px;
  }
}

.success-message {
  text-align: center;

  .dev-url {
    margin-top: 12px;
  }

  .reset-link {
    color: #0095ff;
    text-decoration: none;
    font-size: 14px;

    &:hover {
      text-decoration: underline;
    }
  }
}

.back-link {
  margin-top: 24px;
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;

  a {
    color: #909399;
    text-decoration: none;
    font-size: 14px;
    display: inline-flex;
    align-items: center;
    gap: 4px;

    &:hover {
      color: #0095ff;
    }
  }
}
</style>
