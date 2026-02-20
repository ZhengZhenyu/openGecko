<template>
  <div class="reset-container">
    <el-card class="reset-card">
      <template #header>
        <div class="card-header">
          <h2>openGecko</h2>
          <p class="subtitle">重置密码</p>
        </div>
      </template>

      <!-- Token invalid -->
      <div v-if="!token" class="error-message">
        <el-result icon="error" title="无效的链接">
          <template #sub-title>
            <p>密码重置链接无效或缺少必要参数。</p>
          </template>
          <template #extra>
            <el-button type="primary" @click="router.push('/forgot-password')">
              重新申请
            </el-button>
          </template>
        </el-result>
      </div>

      <!-- Reset success -->
      <div v-else-if="resetSuccess" class="success-message">
        <el-result icon="success" title="密码重置成功">
          <template #sub-title>
            <p>您的密码已成功重置，请使用新密码登录。</p>
          </template>
          <template #extra>
            <el-button type="primary" @click="router.push('/login')">
              前往登录
            </el-button>
          </template>
        </el-result>
      </div>

      <!-- Reset form -->
      <div v-else>
        <p class="description">请输入您的新密码。</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          label-width="0"
          class="reset-form"
        >
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="新密码（至少6位）"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认新密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleReset"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="reset-button"
              @click="handleReset"
            >
              {{ loading ? '重置中...' : '重置密码' }}
            </el-button>
          </el-form-item>
        </el-form>
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
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, ArrowLeft } from '@element-plus/icons-vue'
import { confirmPasswordReset } from '../api/auth'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const resetSuccess = ref(false)

// Get token from URL query
const token = ref((route.query.token as string) || '')

const form = reactive({
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const formRules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleReset = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    await confirmPasswordReset(token.value, form.password)
    resetSuccess.value = true
    ElMessage.success('密码重置成功！')
  } catch (error: any) {
    console.error('Password reset failed:', error)
    ElMessage.error(error.response?.data?.detail || '密码重置失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.reset-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.reset-card {
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

.reset-form {
  .el-form-item {
    margin-bottom: 24px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .reset-button {
    width: 100%;
    margin-top: 12px;
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
