<template>
  <div class="community-care-panel">
    <!-- 导入工具栏 -->
    <div class="import-bar section-card">
      <div class="import-bar-header">
        <h3 class="section-title">🤝 成员导入</h3>
        <div class="import-actions">
          <el-button size="small" type="primary" @click="openCommitteeImport">
            <el-icon><Download /></el-icon> 从委员会导入
          </el-button>
          <el-tooltip content="下载导入模板（CSV 格式，可用 Excel 打开）：姓名(必填)、邮箱、手机号、公司、GitHub账号、备注">
            <el-button size="small" @click="downloadTemplate">
              <el-icon><Document /></el-icon> 下载模板
            </el-button>
          </el-tooltip>
          <el-upload
            :show-file-list="false"
            accept=".csv,.xlsx,.xls"
            :before-upload="handleCsvUpload"
          >
            <el-button size="small">
              <el-icon><Upload /></el-icon> 导入 Excel/CSV
            </el-button>
          </el-upload>
          <el-button size="small" @click="showAddContact = true">
            <el-icon><Plus /></el-icon> 手动添加
          </el-button>
        </div>
      </div>
      <p class="import-hint">关怀对象总数：<strong>{{ total }}</strong> 人</p>
    </div>

    <!-- 联系人列表 -->
    <div class="section-card">
      <div class="section-header">
        <h3 class="section-title">关怀人员列表</h3>
        <FunnelCard :funnel="localFunnel" />
      </div>
      <ContactsTable
        :contacts="contacts"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        @follow-up="openFollowUp"
        @status-change="handleStatusChange"
        @page-change="onPageChange"
        @status-filter="onStatusFilter"
      />
    </div>

    <!-- 从委员会导入 Dialog -->
    <el-dialog v-model="showCommitteeImport" title="从委员会导入成员" width="520px" destroy-on-close>
      <div v-loading="loadingCommittees">
        <p class="dialog-hint">
          选择一个或多个委员会，系统将自动导入其成员（重复成员自动去重）。
          <span v-if="!campaign.community_id" class="warn-text">⚠️ 该活动未关联社区，无法加载委员会</span>
        </p>

        <el-checkbox-group v-model="selectedCommitteeIds">
          <div
            v-for="c in availableCommittees"
            :key="c.id"
            class="committee-item"
          >
            <el-checkbox :label="c.id">
              <span class="committee-name">{{ c.name }}</span>
              <el-tag size="small" type="info" style="margin-left: 8px">{{ c.member_count }} 人</el-tag>
            </el-checkbox>
          </div>
        </el-checkbox-group>

        <div v-if="availableCommittees.length === 0 && !loadingCommittees" class="empty-hint">
          暂无可用委员会
        </div>
      </div>
      <template #footer>
        <el-button @click="showCommitteeImport = false">取消</el-button>
        <el-button
          type="primary"
          :loading="importingCommittee"
          :disabled="selectedCommitteeIds.length === 0"
          @click="handleCommitteeImport"
        >
          导入选中委员会 ({{ selectedCommitteeIds.length }})
        </el-button>
      </template>
    </el-dialog>

    <!-- 手动添加 Dialog -->
    <el-dialog v-model="showAddContact" title="手动添加关怀人员" width="440px" destroy-on-close>
      <el-form :model="addForm" label-width="90px">
        <el-form-item label="姓名" required>
          <el-input v-model="addForm.display_name" placeholder="关怀人员姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="addForm.email" placeholder="email（用于匹配已有档案）" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="addForm.phone" />
        </el-form-item>
        <el-form-item label="公司/组织">
          <el-input v-model="addForm.company" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddContact = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="handleManualAdd">添加</el-button>
      </template>
    </el-dialog>

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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document, Upload, Plus } from '@element-plus/icons-vue'
import {
  listContacts,
  updateContactStatus,
  getCampaignFunnel,
  listAvailableCommittees,
  importFromCommittees,
  importFromCsv,
} from '../../api/campaign'
import type { CampaignDetail, CampaignFunnel, ContactOut, CommitteeSimple } from '../../api/campaign'
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

// 委员会导入
const showCommitteeImport = ref(false)
const loadingCommittees = ref(false)
const importingCommittee = ref(false)
const availableCommittees = ref<CommitteeSimple[]>([])
const selectedCommitteeIds = ref<number[]>([])

// 手动添加
const showAddContact = ref(false)
const adding = ref(false)
const addForm = ref({ display_name: '', email: '', phone: '', company: '', notes: '' })

// 跟进
const showFollowUp = ref(false)
const activeContact = ref<ContactOut | null>(null)

// ─── 加载 ────────────────────────────────────────────────────────────────────
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

// ─── 委员会导入 ────────────────────────────────────────────────────────────────
async function openCommitteeImport() {
  showCommitteeImport.value = true
  selectedCommitteeIds.value = []
  if (availableCommittees.value.length > 0) return
  loadingCommittees.value = true
  try {
    availableCommittees.value = await listAvailableCommittees(props.campaign.id)
  } catch { ElMessage.error('加载委员会失败') } finally { loadingCommittees.value = false }
}

async function handleCommitteeImport() {
  if (selectedCommitteeIds.value.length === 0) return
  importingCommittee.value = true
  try {
    const r = await importFromCommittees(props.campaign.id, {
      committee_ids: selectedCommitteeIds.value,
    })
    ElMessage.success(`已导入 ${r.created} 人，跳过重复 ${r.skipped} 人`)
    showCommitteeImport.value = false
    loadContacts()
  } catch { ElMessage.error('导入失败') } finally { importingCommittee.value = false }
}

// ─── CSV 导入 ─────────────────────────────────────────────────────────────────
async function handleCsvUpload(file: File) {
  try {
    const r = await importFromCsv(props.campaign.id, file)
    const msg = `新建 ${r.created} 条，匹配已有 ${r.matched} 条，跳过重复 ${r.skipped} 条`
    if (r.errors.length > 0) {
      ElMessage.warning(msg + `，${r.errors.length} 行有错误`)
    } else {
      ElMessage.success(msg)
    }
    loadContacts()
  } catch { ElMessage.error('CSV 导入失败') }
  return false // 阻止自动上传
}

// ─── 手动添加 ─────────────────────────────────────────────────────────────────
async function handleManualAdd() {
  if (!addForm.value.display_name.trim()) { ElMessage.warning('请填写姓名'); return }
  adding.value = true
  try {
    // 使用 CSV 导入接口复用逻辑：创建单行 CSV 并上传
    const csvContent = `display_name,email,phone,company,notes\n${
      [
        addForm.value.display_name,
        addForm.value.email,
        addForm.value.phone,
        addForm.value.company,
        addForm.value.notes,
      ]
        .map((v) => `"${(v ?? '').replace(/"/g, '""')}"`)
        .join(',')
    }`
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const file = new File([blob], 'manual.csv', { type: 'text/csv' })
    const r = await importFromCsv(props.campaign.id, file)
    if (r.created + r.matched > 0) {
      ElMessage.success('已添加关怀人员')
      showAddContact.value = false
      addForm.value = { display_name: '', email: '', phone: '', company: '', notes: '' }
      loadContacts()
    } else {
      ElMessage.warning('该人员已在列表中')
    }
  } catch { ElMessage.error('添加失败') } finally { adding.value = false }
}

// ─── CSV 模板下载 ─────────────────────────────────────────────────────────────
function downloadTemplate() {
  const header = 'display_name,email,phone,company,github_handle,notes'
  const desc   = '姓名(必填),邮箱(用于去重匹配),手机号,所在公司,GitHub账号,备注'
  const rows = [
    '张三,zhangsan@example.com,13812345678,开放原子开源基金会,zhangsan_oa,核心委员',
    '李四,lisi@example.com,,某科技公司,lisi_dev,',
    '王五,,13900000000,自由职业,,',
  ]
  const content = [header, desc, ...rows].join('\n') + '\n'
  const blob = new Blob(['\uFEFF' + content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'community_care_template.csv'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadContacts()
  // 预加载委员会列表
  if (props.campaign.community_id) {
    listAvailableCommittees(props.campaign.id)
      .then((list) => { availableCommittees.value = list })
      .catch(() => {})
  }
})
</script>

<style scoped>
.community-care-panel {
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

.import-bar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.import-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.import-hint {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.warn-text {
  color: #f59e0b;
  margin-left: 8px;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 14px;
}

.dialog-hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.committee-item {
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.committee-item:last-child {
  border-bottom: none;
}

.committee-name {
  font-size: 14px;
  color: #1e293b;
}

.empty-hint {
  text-align: center;
  padding: 32px;
  color: #94a3b8;
  font-size: 13px;
}
</style>
