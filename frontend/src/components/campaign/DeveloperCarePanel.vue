<template>
  <div class="developer-care-panel">
    <!-- 顶部统计 -->
    <div class="stats-bar section-card">
      <div class="stat-item">
        <span class="stat-value">{{ total }}</span>
        <span class="stat-label">已导入开发者</span>
      </div>
      <div class="stat-item" v-if="localFunnel">
        <span class="stat-value text-blue">{{ localFunnel.contacted }}</span>
        <span class="stat-label">已联系</span>
      </div>
      <div class="stat-item" v-if="localFunnel">
        <span class="stat-value text-orange">{{ localFunnel.blocked }}</span>
        <span class="stat-label">阻塞中</span>
      </div>
      <div class="stat-item" v-if="localFunnel">
        <span class="stat-value">{{ localFunnel.pending }}</span>
        <span class="stat-label">待联系</span>
      </div>
    </div>

    <!-- CSV/Excel 导入区 -->
    <div class="section-card upload-card">
      <div class="upload-header">
        <div>
          <h3 class="section-title">📤 批量导入开发者</h3>
          <p class="upload-desc">支持 CSV / Excel 文件，每次最多 5000 行</p>
        </div>
        <el-tooltip content="下载导入模板（CSV 格式，可用 Excel 打开）：姓名(必填)、邮箱、手机号、公司、GitHub账号、备注">
          <el-button size="small" @click="downloadTemplate">
            <el-icon><Download /></el-icon> 下载模板
          </el-button>
        </el-tooltip>
      </div>

      <el-upload
        drag
        :show-file-list="false"
        accept=".csv,.xlsx,.xls"
        :before-upload="handleCsvUpload"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 CSV / Excel（.xlsx）格式，最多 5000 行。
            必填列：<strong>display_name</strong>（姓名）；选填：email（邮箱，用于去重）、phone、company、github_handle、notes。
            建议先下载模板查看格式示例。
          </div>
        </template>
      </el-upload>

      <!-- 导入结果 -->
      <div v-if="lastImportResult" class="import-result">
        <el-alert
          :type="lastImportResult.errors.length > 0 ? 'warning' : 'success'"
          :closable="false"
        >
          <template #title>
            <span>
              本次导入：新建 <strong>{{ lastImportResult.created }}</strong> 条，
              匹配已有 <strong>{{ lastImportResult.matched }}</strong> 条，
              跳过重复 <strong>{{ lastImportResult.skipped }}</strong> 条
            </span>
          </template>
          <div v-if="lastImportResult.errors.length > 0" style="margin-top: 6px">
            <div v-for="(e, i) in lastImportResult.errors.slice(0, 5)" :key="i" class="error-row">
              ⚠️ {{ e }}
            </div>
            <div v-if="lastImportResult.errors.length > 5" style="color: #94a3b8; font-size: 12px">
              ... 共 {{ lastImportResult.errors.length }} 条错误
            </div>
          </div>
        </el-alert>
      </div>
    </div>

    <!-- 漏斗图 -->
    <div class="section-card" v-if="localFunnel">
      <h3 class="section-title" style="margin-bottom: 12px">转化漏斗</h3>
      <FunnelCard :funnel="localFunnel" />
    </div>

    <!-- 开发者列表 -->
    <div class="section-card">
      <div class="list-header">
        <h3 class="section-title">开发者列表</h3>
      </div>
      <ContactsTable
        :contacts="contacts"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        @follow-up="openFollowUp"
        @status-change="handleStatusChange"
        @batch-status-change="handleBatchStatus"
        @page-change="onPageChange"
        @status-filter="onStatusFilter"
      />
    </div>

    <!-- 跟进弹窗 -->
    <FollowUpDialog
      v-model="showFollowUp"
      :campaign-id="campaign.id"
      :contact="activeContact"
      @saved="loadContacts"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, UploadFilled } from '@element-plus/icons-vue'
import {
  listContacts,
  updateContactStatus,
  getCampaignFunnel,
  importFromCsv,
  updateCampaign,
  bulkUpdateContactStatus,
} from '../../api/campaign'
import type { CampaignDetail, CampaignFunnel, ContactOut, CsvImportResult } from '../../api/campaign'
import ContactsTable from './ContactsTable.vue'
import FunnelCard from './FunnelCard.vue'
import FollowUpDialog from './FollowUpDialog.vue'

const props = defineProps<{ campaign: CampaignDetail }>()
const emit = defineEmits<{ (e: 'reload'): void }>()

const loading = ref(false)
const contacts = ref<ContactOut[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const statusFilter = ref('')
const localFunnel = ref<CampaignFunnel | null>(null)
const lastImportResult = ref<CsvImportResult | null>(null)
const showFollowUp = ref(false)
const activeContact = ref<ContactOut | null>(null)

// 批量状态更新
async function handleBatchStatus(contactIds: number[], status: string) {
  try {
    const r = await bulkUpdateContactStatus(props.campaign.id, { contact_ids: contactIds, status })
    ElMessage.success(`已批量更新 ${r.updated} 条记录`)
    loadContacts()
  } catch { ElMessage.error('批量更新失败') }
}

// ─── 加载 ─────────────────────────────────────────────────────────────────────
async function loadContacts() {
  loading.value = true
  try {
    const res = await listContacts(props.campaign.id, {
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    contacts.value = res.items
    total.value = res.total
    localFunnel.value = await getCampaignFunnel(props.campaign.id)
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) { page.value = p; loadContacts() }
function onStatusFilter(s: string) { statusFilter.value = s; page.value = 1; loadContacts() }

async function handleStatusChange(contact: ContactOut, status: string) {
  try {
    const updated = await updateContactStatus(props.campaign.id, contact.id, { status })
    const idx = contacts.value.findIndex((c) => c.id === contact.id)
    if (idx !== -1) contacts.value[idx] = updated
    localFunnel.value = await getCampaignFunnel(props.campaign.id)
  } catch { ElMessage.error('状态更新失败') }
}

function openFollowUp(contact: ContactOut) {
  activeContact.value = contact
  showFollowUp.value = true
}

// ─── CSV 导入 ─────────────────────────────────────────────────────────────────
async function handleCsvUpload(file: File) {
  try {
    const r = await importFromCsv(props.campaign.id, file)
    lastImportResult.value = r
    if (r.errors.length === 0) {
      ElMessage.success(`导入完成：新建 ${r.created}，匹配 ${r.matched}，跳过 ${r.skipped}`)
    } else {
      ElMessage.warning(`导入完成，${r.errors.length} 行有错误，请查看报告`)
    }
    loadContacts()
  } catch { ElMessage.error('文件导入失败，请检查格式') }
  return false // 阻止 el-upload 自动上传
}

// ─── CSV 模板下载 ─────────────────────────────────────────────────────────────
function downloadTemplate() {
  const header = 'display_name,email,phone,company,github_handle,notes'
  const desc   = '姓名(必填),邮箱(用于去重匹配),手机号,所在公司,GitHub账号,备注'
  const rows = [
    '张三,zhangsan@example.com,13812345678,某科技公司,zhangsan_dev,活跃贡献者',
    '李四,lisi@example.com,,开放原子开源基金会,lisi_oa,',
    '王五,,13900000000,自由职业,,',
  ]
  const content = [header, desc, ...rows].join('\n') + '\n'
  const blob = new Blob(['\uFEFF' + content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'developer_care_template.csv'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadContacts()
})
</script>

<style scoped>
.developer-care-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

/* 顶部统计条 */
.stats-bar {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.owner-stat {
  flex-direction: row;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.owner-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.1;
}

.stat-value.text-blue { color: #0095ff; }
.stat-value.text-green { color: #22c55e; }
.stat-value.text-orange { color: #f59e0b; }

.stat-label {
  font-size: 12px;
  color: #94a3b8;
}

/* 上传区 */
.upload-card {}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.upload-desc {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.import-result {
  margin-top: 12px;
}

.error-row {
  font-size: 12px;
  color: #b45309;
  line-height: 1.6;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>
