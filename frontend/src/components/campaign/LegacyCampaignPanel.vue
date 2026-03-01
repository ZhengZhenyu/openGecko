<template>
  <el-row :gutter="20">
    <!-- 漏斗 + 导入 -->
    <el-col :span="7">
      <div class="section-card">
        <FunnelCard :funnel="funnel" />
        <div class="import-actions">
          <p class="import-title">导入联系人</p>
          <el-button size="small" style="width: 100%; margin-bottom: 8px" @click="showImportEvent = true">
            <el-icon><Flag /></el-icon> 从活动签到导入
          </el-button>
          <el-button size="small" style="width: 100%" @click="showAddContact = true">
            <el-icon><Plus /></el-icon> 手动添加
          </el-button>
        </div>
      </div>
    </el-col>

    <!-- 联系人列表 -->
    <el-col :span="17">
      <div class="section-card">
        <div class="section-header">
          <h3 class="section-title">联系人列表</h3>
        </div>
        <ContactsTable
          :contacts="contacts"
          :total="total"
          :page="page"
          :page-size="pageSize"
          :loading="contactsLoading"
          @follow-up="openFollowUp"
          @status-change="handleStatusChange"
          @page-change="onPageChange"
          @status-filter="onStatusFilter"
        />
      </div>
    </el-col>
  </el-row>

  <!-- 从活动导入 -->
  <el-dialog v-model="showImportEvent" title="从活动签到导入" width="400px" destroy-on-close>
    <el-form :model="importEventForm" label-width="80px">
      <el-form-item label="活动 ID" required>
        <el-input-number v-model="importEventForm.event_id" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item label="沟通渠道">
        <el-select v-model="importEventForm.channel" clearable style="width: 100%">
          <el-option v-for="ch in channels" :key="ch" :label="ch" :value="ch" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showImportEvent = false">取消</el-button>
      <el-button type="primary" :loading="importing" @click="handleImportEvent">导入</el-button>
    </template>
  </el-dialog>

  <!-- 手动添加 -->
  <el-dialog v-model="showAddContact" title="手动添加联系人" width="400px" destroy-on-close>
    <el-form :model="addForm" label-width="90px">
      <el-form-item label="人脉 ID" required>
        <el-input-number v-model="addForm.person_id" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item label="沟通渠道">
        <el-select v-model="addForm.channel" clearable style="width: 100%">
          <el-option v-for="ch in channels" :key="ch" :label="ch" :value="ch" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="addForm.notes" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddContact = false">取消</el-button>
      <el-button type="primary" :loading="adding" @click="handleAddContact">添加</el-button>
    </template>
  </el-dialog>

  <!-- 跟进弹窗 -->
  <FollowUpDialog
    v-model="showFollowUp"
    :campaign-id="campaign.id"
    :contact="activeContact"
    @saved="loadContacts"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Flag, Plus } from '@element-plus/icons-vue'
import {
  listContacts,
  addContact,
  updateContactStatus,
  importFromEvent,
  getCampaignFunnel,
} from '../../api/campaign'
import type { CampaignDetail, CampaignFunnel, ContactOut } from '../../api/campaign'
import ContactsTable from './ContactsTable.vue'
import FunnelCard from './FunnelCard.vue'
import FollowUpDialog from './FollowUpDialog.vue'

const props = defineProps<{
  campaign: CampaignDetail
  funnel: CampaignFunnel | null
}>()
const emit = defineEmits<{ (e: 'reload'): void }>()

const contactsLoading = ref(false)
const contacts = ref<ContactOut[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const statusFilter = ref('')

const showImportEvent = ref(false)
const showAddContact = ref(false)
const showFollowUp = ref(false)
const importing = ref(false)
const adding = ref(false)
const activeContact = ref<ContactOut | null>(null)

const importEventForm = ref({ event_id: 0, channel: '' })
const addForm = ref({ person_id: 0, channel: '', notes: '' })
const channels = ['email', 'wechat', 'phone', 'in_person', 'other']

async function loadContacts() {
  contactsLoading.value = true
  try {
    const res = await listContacts(props.campaign.id, {
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    contacts.value = res.items
    total.value = res.total
  } finally {
    contactsLoading.value = false
  }
}

function onPageChange(p: number) { page.value = p; loadContacts() }
function onStatusFilter(s: string) { statusFilter.value = s; page.value = 1; loadContacts() }

async function handleStatusChange(contact: ContactOut, status: string) {
  try {
    const updated = await updateContactStatus(props.campaign.id, contact.id, { status })
    const idx = contacts.value.findIndex((c) => c.id === contact.id)
    if (idx !== -1) contacts.value[idx] = updated
    emit('reload')
  } catch { ElMessage.error('状态更新失败') }
}

function openFollowUp(contact: ContactOut) {
  activeContact.value = contact
  showFollowUp.value = true
}

async function handleImportEvent() {
  if (!importEventForm.value.event_id) { ElMessage.warning('请输入活动 ID'); return }
  importing.value = true
  try {
    const r = await importFromEvent(props.campaign.id, {
      event_id: importEventForm.value.event_id,
      channel: importEventForm.value.channel || undefined,
    })
    ElMessage.success(`已导入 ${r.created} 人，跳过 ${r.skipped} 人`)
    showImportEvent.value = false
    loadContacts(); emit('reload')
  } catch { ElMessage.error('导入失败') } finally { importing.value = false }
}

async function handleAddContact() {
  if (!addForm.value.person_id) { ElMessage.warning('请输入人脉 ID'); return }
  adding.value = true
  try {
    await addContact(props.campaign.id, {
      person_id: addForm.value.person_id,
      channel: addForm.value.channel || undefined,
      notes: addForm.value.notes || undefined,
    })
    showAddContact.value = false
    ElMessage.success('已添加联系人')
    loadContacts(); emit('reload')
  } catch { ElMessage.error('添加失败') } finally { adding.value = false }
}

onMounted(loadContacts)
</script>

<style scoped>
.section-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.import-actions {
  border-top: 1px solid #f1f5f9;
  padding-top: 14px;
  margin-top: 16px;
}

.import-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}
</style>
