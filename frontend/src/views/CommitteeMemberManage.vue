<template>
  <div class="member-manage">
    <div class="page-title">
      <div>
        <h2>成员批量管理</h2>
        <p class="subtitle">批量导入或导出委员会成员</p>
      </div>
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <!-- Committee Selection -->
    <div class="section-card selection-card">
      <el-form :inline="true">
        <el-form-item label="选择委员会">
          <el-select
            v-model="selectedCommitteeId"
            placeholder="请选择委员会"
            style="width: 300px"
            @change="handleCommitteeChange"
          >
            <el-option
              v-for="committee in committees"
              :key="committee.id"
              :label="committee.name"
              :value="committee.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="selectedCommitteeId">
      <el-row :gutter="24">
        <!-- Export Section -->
        <el-col :xs="24" :md="12">
          <el-card class="section-card action-card">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><Download /></el-icon>
                <span>导出成员</span>
              </div>
            </template>

            <div class="action-content">
              <p class="description">
                将当前委员会的所有成员导出为CSV文件，可用于备份或在其他系统中使用。
              </p>

              <div class="stats">
                <div class="stat-item">
                  <div class="stat-value">{{ memberCount }}</div>
                  <div class="stat-label">当前成员数</div>
                </div>
              </div>

              <el-button
                type="primary"
                :loading="exporting"
                @click="exportMembers"
              >
                <el-icon><Download /></el-icon>
                导出为CSV
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- Import Section -->
        <el-col :xs="24" :md="12">
          <el-card class="section-card action-card">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><Upload /></el-icon>
                <span>导入成员</span>
              </div>
            </template>

            <div class="action-content">
              <p class="description">
                从CSV文件批量导入成员。请确保文件格式正确，第一行为表头。
              </p>

              <div class="file-requirements">
                <div class="requirement-title">CSV格式要求：</div>
                <ul>
                  <li><strong>name</strong>（必填）：成员姓名</li>
                  <li>email：电子邮箱</li>
                  <li>phone：联系电话</li>
                  <li>wechat：微信号</li>
                  <li>organization：所属组织</li>
                  <li>roles：角色（逗号分隔，如：chair,secretary）</li>
                  <li>term_start：任期开始（YYYY-MM-DD）</li>
                  <li>term_end：任期结束（YYYY-MM-DD）</li>
                  <li>is_active：是否在任（true/false）</li>
                  <li>bio：个人简介</li>
                </ul>
              </div>

              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                accept=".csv"
                :on-change="handleFileChange"
                :file-list="fileList"
              >
                <el-button>
                  <el-icon><Folder /></el-icon>
                  选择CSV文件
                </el-button>
              </el-upload>

              <el-button
                v-if="fileList.length > 0"
                type="primary"
                :loading="importing"
                @click="importMembers"
                style="margin-top: 12px"
              >
                <el-icon><Upload /></el-icon>
                开始导入
              </el-button>

              <el-button
                type="info"
                link
                @click="downloadTemplate"
              >
                <el-icon><Download /></el-icon>
                下载CSV模板
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Import Result -->
      <el-card v-if="importResult" class="section-card result-card">
        <template #header>
          <span>导入结果</span>
        </template>

        <el-result
          :icon="importResult.error_count === 0 ? 'success' : 'warning'"
          :title="getResultTitle()"
        >
          <template #sub-title>
            <div class="result-stats">
              <div class="result-stat success">
                <el-icon><SuccessFilled /></el-icon>
                成功导入: {{ importResult.success_count }} 条
              </div>
              <div v-if="importResult.error_count > 0" class="result-stat error">
                <el-icon><CircleCloseFilled /></el-icon>
                失败: {{ importResult.error_count }} 条
              </div>
            </div>

            <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
              <el-divider />
              <div class="error-title">错误详情：</div>
              <ul>
                <li v-for="(error, index) in importResult.errors" :key="index">
                  {{ error }}
                </li>
              </ul>
            </div>
          </template>

          <template #extra>
            <el-button type="primary" @click="importResult = null">
              关闭
            </el-button>
            <el-button @click="$router.push(`/committees/${selectedCommitteeId}`)">
              查看委员会
            </el-button>
          </template>
        </el-result>
      </el-card>
    </div>

    <el-empty
      v-else
      description="请先选择一个委员会"
      :image-size="120"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile, type UploadInstance } from 'element-plus'
import {
  ArrowLeft,
  Download,
  Upload,
  Folder,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { listCommittees, getCommittee, type Committee, type CommitteeWithMembers } from '@/api/governance'
import { useCommunityStore } from '@/stores/community'
import apiClient from '@/api/index'

const router = useRouter()
const communityStore = useCommunityStore()

const committees = ref<Committee[]>([])
const selectedCommitteeId = ref<number | undefined>()
const selectedCommittee = ref<CommitteeWithMembers | null>(null)

const exporting = ref(false)
const importing = ref(false)
const fileList = ref<UploadFile[]>([])
const uploadRef = ref<UploadInstance>()

interface ImportResult {
  success_count: number
  error_count: number
  errors: string[]
}

const importResult = ref<ImportResult | null>(null)

const memberCount = computed(() => {
  return selectedCommittee.value?.member_count || 0
})

onMounted(() => {
  // Ensure community ID is set from store
  const currentCommunityId = communityStore.currentCommunityId
  if (currentCommunityId) {
    localStorage.setItem('current_community_id', String(currentCommunityId))
  }
  loadCommittees()
})

async function loadCommittees() {
  try {
    committees.value = await listCommittees()
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会失败')
  }
}

async function handleCommitteeChange() {
  if (!selectedCommitteeId.value) {
    selectedCommittee.value = null
    return
  }

  try {
    // Set current community ID for API calls
    const committee = committees.value.find(c => c.id === selectedCommitteeId.value)
    if (committee) {
      localStorage.setItem('current_community_id', String(committee.community_id))
    }
    selectedCommittee.value = await getCommittee(selectedCommitteeId.value)
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会详情失败')
  }
}

async function exportMembers() {
  if (!selectedCommitteeId.value) return

  exporting.value = true
  try {
    // Ensure community ID is set before making request
    const committee = committees.value.find(c => c.id === selectedCommitteeId.value)
    if (committee) {
      localStorage.setItem('current_community_id', String(committee.community_id))
    }

    const response = await apiClient.get(`/committees/${selectedCommitteeId.value}/members/export`, {
      responseType: 'blob'
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${committee?.slug || 'members'}_members.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

function handleFileChange(file: UploadFile) {
  fileList.value = [file]
  importResult.value = null
}

async function importMembers() {
  if (!selectedCommitteeId.value || fileList.value.length === 0) return

  const file = fileList.value[0].raw
  if (!file) {
    ElMessage.error('请选择文件')
    return
  }

  importing.value = true
  try {
    // Ensure community ID is set before making request
    const committee = committees.value.find(c => c.id === selectedCommitteeId.value)
    if (committee) {
      localStorage.setItem('current_community_id', String(committee.community_id))
    }

    const formData = new FormData()
    formData.append('file', file)

    const { data: result } = await apiClient.post<ImportResult>(`/committees/${selectedCommitteeId.value}/members/import`, formData)

    importResult.value = result

    if (result.error_count === 0) {
      ElMessage.success(`成功导入 ${result.success_count} 条成员记录`)
    } else {
      ElMessage.warning(`导入完成，成功 ${result.success_count} 条，失败 ${result.error_count} 条`)
    }

    // Clear file list
    fileList.value = []
    uploadRef.value?.clearFiles()

    // Refresh committee data
    if (result.success_count > 0) {
      handleCommitteeChange()
    }
  } catch (error: any) {
    ElMessage.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

function downloadTemplate() {
  // Create CSV template
  const template = [
    ['name', 'email', 'phone', 'wechat', 'organization', 'roles', 'term_start', 'term_end', 'is_active', 'bio'],
    ['张三', 'zhangsan@example.com', '13800138000', 'zhangsan_wx', '示例公司', 'chair,secretary', '2024-01-01', '2025-12-31', 'true', '示例成员简介'],
    ['李四', 'lisi@example.com', '', '', '另一家公司', 'member', '2024-01-01', '', 'true', '']
  ]

  const csvContent = template.map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'members_template.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

function getResultTitle() {
  if (!importResult.value) return ''
  if (importResult.value.error_count === 0) {
    return '导入成功！'
  }
  return '导入部分成功'
}
</script>

<style scoped>
.member-manage {
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
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.section-card {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}

.section-card:hover {
  box-shadow: var(--shadow-hover);
}

.action-card {
  margin-bottom: 24px;
  height: calc(100% - 24px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-icon {
  font-size: 20px;
  color: var(--blue);
}

.action-content {
  min-height: 300px;
}

.description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
  font-size: 14px;
}

.stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--blue);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.file-requirements {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
  font-size: 14px;
}

.requirement-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.file-requirements ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.file-requirements li {
  margin-bottom: 4px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.result-card {
  margin-top: 24px;
}

.result-stats {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-top: 16px;
}

.result-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.result-stat.success {
  color: var(--green);
}

.result-stat.error {
  color: var(--red);
}

.error-list {
  margin-top: 16px;
  text-align: left;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.error-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.error-list ul {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
}

.error-list li {
  margin-bottom: 4px;
  line-height: 1.6;
}

/* Element Plus overrides */
:deep(.el-card) {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

:deep(.el-card__header) {
  border-bottom: 1px solid #f1f5f9;
  padding: 18px 24px;
}

:deep(.el-card__body) {
  padding: 24px;
}

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

:deep(.el-upload-dragger) {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  background: #f8fafc;
  transition: all 0.2s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--blue);
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
</style>
