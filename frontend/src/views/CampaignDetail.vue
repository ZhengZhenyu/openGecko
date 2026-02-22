<template>
  <div v-loading="loading" class="campaign-detail">
    <template v-if="campaign">
      <!-- Header -->
      <div class="detail-header">
        <el-button link @click="$router.push('/campaigns')">
          <el-icon><ArrowLeft /></el-icon>
          返回运营活动
        </el-button>
      </div>

      <!-- Info Card -->
      <div class="info-card">
        <div class="info-top">
          <div class="info-title-row">
            <h1 class="campaign-title">{{ campaign.name }}</h1>
            <div class="info-badges">
              <el-tag :type="typeTagMap[campaign.type] ?? 'info'">{{ typeLabel[campaign.type] ?? campaign.type }}</el-tag>
              <el-tag :type="statusTagMap[campaign.status] ?? 'info'">{{ statusLabel[campaign.status] ?? campaign.status }}</el-tag>
            </div>
          </div>
          <el-select v-model="campaign.status" size="small" style="width: 110px" @change="handleStatusChange">
            <el-option v-for="(label, val) in statusLabel" :key="val" :label="label" :value="val" />
          </el-select>
        </div>
        <p v-if="campaign.description" class="campaign-desc">{{ campaign.description }}</p>
        <div class="info-meta">
          <span v-if="campaign.target_count"><el-icon><User /></el-icon> 目标 {{ campaign.target_count }} 人</span>
          <span v-if="campaign.start_date"><el-icon><Calendar /></el-icon> {{ campaign.start_date }} ~ {{ campaign.end_date || '待定' }}</span>
        </div>
      </div>

      <!-- Funnel + Contacts -->
      <el-row :gutter="20" class="main-content">
        <!-- Funnel Card -->
        <el-col :span="7">
          <div class="funnel-card section-card">
            <h3 class="section-title">转化漏斗</h3>
            <div v-if="funnel" class="funnel-list">
              <div v-for="step in funnelSteps" :key="step.key" class="funnel-item">
                <div class="funnel-label">
                  <span class="funnel-dot" :style="{ background: step.color }" />
                  {{ step.label }}
                </div>
                <div class="funnel-bar-wrap">
                  <div
                    class="funnel-bar"
                    :style="{
                      width: funnel.total ? (funnel[step.key] / funnel.total * 100) + '%' : '0%',
                      background: step.color,
                    }"
                  />
                </div>
                <span class="funnel-count">{{ funnel[step.key] }}</span>
              </div>
              <div class="funnel-total">共 {{ funnel.total }} 人</div>
            </div>
            <div v-else class="funnel-empty">暂无数据</div>

            <!-- Quick Import -->
            <div class="import-actions">
              <h4 class="import-title">导入联系人</h4>
              <el-button size="small" style="width: 100%; margin-bottom: 8px" @click="showImportEventDialog = true">
                <el-icon><Flag /></el-icon> 从活动签到导入
              </el-button>
              <el-button size="small" style="width: 100%" @click="showAddContactDialog = true">
                <el-icon><Plus /></el-icon> 手动添加
              </el-button>
            </div>
          </div>
        </el-col>

        <!-- Contacts Table -->
        <el-col :span="17">
          <div class="section-card">
            <div class="section-header">
              <h3 class="section-title">联系人列表</h3>
              <div class="section-filters">
                <el-select v-model="contactStatus" placeholder="状态" clearable size="small" style="width: 110px" @change="loadContacts">
                  <el-option v-for="(label, val) in contactStatusLabel" :key="val" :label="label" :value="val" />
                </el-select>
              </div>
            </div>
            <el-table v-loading="contactsLoading" :data="contacts" style="width: 100%">
              <el-table-column label="姓名" min-width="130">
                <template #default="{ row }">
                  {{ row.person?.display_name ?? '-' }}
                </template>
              </el-table-column>
              <el-table-column label="公司" min-width="130">
                <template #default="{ row }">{{ row.person?.company ?? '-' }}</template>
              </el-table-column>
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <el-tag :type="contactStatusTagMap[row.status] ?? 'info'" size="small">
                    {{ contactStatusLabel[row.status] ?? row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="渠道" prop="channel" width="90">
                <template #default="{ row }">{{ row.channel ?? '-' }}</template>
              </el-table-column>
              <el-table-column label="最近跟进" width="130">
                <template #default="{ row }">{{ row.last_contacted_at ? formatDate(row.last_contacted_at) : '-' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="130">
                <template #default="{ row }">
                  <el-button link size="small" @click="openActivityDialog(row)">跟进</el-button>
                  <el-select
                    :model-value="row.status"
                    size="small"
                    style="width: 72px"
                    @change="(v: string) => handleContactStatusChange(row, v)"
                  >
                    <el-option v-for="(label, val) in contactStatusLabel" :key="val" :label="label" :value="val" />
                  </el-select>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="contactTotal > contactPageSize"
              v-model:current-page="contactPage"
              :page-size="contactPageSize"
              :total="contactTotal"
              layout="prev, pager, next"
              style="margin-top: 12px; display: flex; justify-content: flex-end"
              @current-change="loadContacts"
            />
          </div>
        </el-col>
      </el-row>
    </template>

    <!-- Import from Event Dialog -->
    <el-dialog v-model="showImportEventDialog" title="从活动签到导入" width="400px" destroy-on-close>
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
        <el-button @click="showImportEventDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImportEvent">导入</el-button>
      </template>
    </el-dialog>

    <!-- Add Contact Dialog -->
    <el-dialog v-model="showAddContactDialog" title="手动添加联系人" width="400px" destroy-on-close>
      <el-form :model="addContactForm" label-width="90px">
        <el-form-item label="人脉 ID" required>
          <el-input-number v-model="addContactForm.person_id" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="沟通渠道">
          <el-select v-model="addContactForm.channel" clearable style="width: 100%">
            <el-option v-for="ch in channels" :key="ch" :label="ch" :value="ch" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addContactForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddContactDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingContact" @click="handleAddContact">添加</el-button>
      </template>
    </el-dialog>

    <!-- Activity Dialog -->
    <el-dialog v-model="showActivityDialog" :title="`跟进记录 — ${activeContact?.person?.display_name ?? ''}`" width="420px" destroy-on-close>
      <el-form :model="activityForm" label-width="80px">
        <el-form-item label="跟进方式" required>
          <el-select v-model="activityForm.action" style="width: 100%">
            <el-option label="发送邮件" value="sent_email" />
            <el-option label="电话沟通" value="made_call" />
            <el-option label="微信联系" value="sent_wechat" />
            <el-option label="面对面会谈" value="in_person_meeting" />
            <el-option label="收到回复" value="got_reply" />
            <el-option label="备注" value="note" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="activityForm.content" type="textarea" :rows="3" placeholder="跟进内容摘要" />
        </el-form-item>
        <el-form-item label="结果">
          <el-input v-model="activityForm.outcome" placeholder="跟进结果/进展" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showActivityDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingActivity" @click="handleAddActivity">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, User, Calendar, Flag, Plus } from '@element-plus/icons-vue'
import {
  getCampaign,
  getCampaignFunnel,
  listContacts,
  addContact,
  updateContactStatus,
  importFromEvent,
  addActivity,
  updateCampaign,
} from '../api/campaign'
import type { CampaignDetail, ContactOut, CampaignFunnel } from '../api/campaign'

const route = useRoute()
const campaignId = computed(() => Number(route.params.id))

const loading = ref(false)
const campaign = ref<CampaignDetail | null>(null)
const funnel = ref<CampaignFunnel | null>(null)

const contactsLoading = ref(false)
const contacts = ref<ContactOut[]>([])
const contactTotal = ref(0)
const contactPage = ref(1)
const contactPageSize = 20
const contactStatus = ref<string>('')

const showImportEventDialog = ref(false)
const showAddContactDialog = ref(false)
const showActivityDialog = ref(false)
const importing = ref(false)
const addingContact = ref(false)
const savingActivity = ref(false)

const activeContact = ref<ContactOut | null>(null)

const importEventForm = ref({ event_id: 0, channel: '' })
const addContactForm = ref({ person_id: 0, channel: '', notes: '' })
const activityForm = ref({ action: 'note', content: '', outcome: '' })

const channels = ['email', 'wechat', 'phone', 'in_person', 'other']

const typeLabel: Record<string, string> = { promotion: '推广宣传', care: '关怀回访', invitation: '邀请加入', survey: '问卷调研' }
const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { promotion: 'primary', care: 'success', invitation: 'warning', survey: 'info' }
const statusLabel: Record<string, string> = { draft: '草稿', active: '进行中', completed: '已完成', archived: '已归档' }
const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { draft: 'info', active: 'primary', completed: 'success', archived: '' }
const contactStatusLabel: Record<string, string> = { pending: '待联系', contacted: '已联系', responded: '已回复', converted: '已转化', declined: '已拒绝' }
const contactStatusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { pending: 'info', contacted: 'primary', responded: 'warning', converted: 'success', declined: 'danger' }

const funnelSteps = [
  { key: 'pending' as keyof CampaignFunnel, label: '待联系', color: '#94a3b8' },
  { key: 'contacted' as keyof CampaignFunnel, label: '已联系', color: '#0095ff' },
  { key: 'responded' as keyof CampaignFunnel, label: '已回复', color: '#f59e0b' },
  { key: 'converted' as keyof CampaignFunnel, label: '已转化', color: '#10b981' },
  { key: 'declined' as keyof CampaignFunnel, label: '已拒绝', color: '#ef4444' },
]

function formatDate(dt: string): string {
  return new Date(dt).toLocaleDateString('zh-CN')
}

async function loadCampaign() {
  loading.value = true
  try {
    const [c, f] = await Promise.all([
      getCampaign(campaignId.value),
      getCampaignFunnel(campaignId.value),
    ])
    campaign.value = c
    funnel.value = f
  } catch {
    ElMessage.error('加载运营活动失败')
  } finally {
    loading.value = false
  }
}

async function loadContacts() {
  contactsLoading.value = true
  try {
    const data = await listContacts(campaignId.value, {
      status: contactStatus.value || undefined,
      page: contactPage.value,
      page_size: contactPageSize,
    })
    contacts.value = data.items
    contactTotal.value = data.total
  } catch {
    /* empty */
  } finally {
    contactsLoading.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  try {
    await updateCampaign(campaignId.value, { status: newStatus })
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleContactStatusChange(contact: ContactOut, newStatus: string) {
  try {
    const updated = await updateContactStatus(campaignId.value, contact.id, { status: newStatus })
    const idx = contacts.value.findIndex(c => c.id === contact.id)
    if (idx !== -1) contacts.value[idx] = updated
    funnel.value = await getCampaignFunnel(campaignId.value)
  } catch {
    ElMessage.error('状态更新失败')
  }
}

async function handleImportEvent() {
  if (!importEventForm.value.event_id) { ElMessage.warning('请输入活动 ID'); return }
  importing.value = true
  try {
    const result = await importFromEvent(campaignId.value, {
      event_id: importEventForm.value.event_id,
      channel: importEventForm.value.channel || undefined,
    })
    ElMessage.success(`已导入 ${result.created} 人，跳过 ${result.skipped} 人`)
    showImportEventDialog.value = false
    await Promise.all([loadContacts(), reloadFunnel()])
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

async function handleAddContact() {
  if (!addContactForm.value.person_id) { ElMessage.warning('请输入人脉 ID'); return }
  addingContact.value = true
  try {
    await addContact(campaignId.value, {
      person_id: addContactForm.value.person_id,
      channel: addContactForm.value.channel || undefined,
      notes: addContactForm.value.notes || undefined,
    })
    showAddContactDialog.value = false
    ElMessage.success('已添加联系人')
    await Promise.all([loadContacts(), reloadFunnel()])
  } catch {
    ElMessage.error('添加失败')
  } finally {
    addingContact.value = false
  }
}

function openActivityDialog(contact: ContactOut) {
  activeContact.value = contact
  activityForm.value = { action: 'note', content: '', outcome: '' }
  showActivityDialog.value = true
}

async function handleAddActivity() {
  if (!activeContact.value) return
  savingActivity.value = true
  try {
    await addActivity(campaignId.value, activeContact.value.id, {
      action: activityForm.value.action,
      content: activityForm.value.content || undefined,
      outcome: activityForm.value.outcome || undefined,
    })
    showActivityDialog.value = false
    ElMessage.success('跟进记录已保存')
    await loadContacts()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingActivity.value = false
  }
}

async function reloadFunnel() {
  funnel.value = await getCampaignFunnel(campaignId.value)
}

onMounted(async () => {
  await loadCampaign()
  await loadContacts()
})
</script>

<style scoped>
.campaign-detail {
  padding: 24px 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.detail-header {
  margin-bottom: 16px;
}

.info-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 20px;
}

.info-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.info-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.campaign-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.info-badges {
  display: flex;
  gap: 6px;
}

.campaign-desc {
  margin: 0 0 10px;
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
}

.info-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #475569;
}

.info-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.main-content {
  margin-top: 0;
}

.section-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px 20px;
}

.section-title {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-filters {
  display: flex;
  gap: 8px;
}

/* Funnel */
.funnel-card {
  height: fit-content;
}

.funnel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.funnel-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.funnel-label {
  display: flex;
  align-items: center;
  gap: 5px;
  width: 72px;
  font-size: 12px;
  color: #475569;
  flex-shrink: 0;
}

.funnel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.funnel-bar-wrap {
  flex: 1;
  height: 10px;
  background: #f1f5f9;
  border-radius: 5px;
  overflow: hidden;
}

.funnel-bar {
  height: 100%;
  border-radius: 5px;
  min-width: 2px;
  transition: width 0.3s;
}

.funnel-count {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  width: 28px;
  text-align: right;
}

.funnel-total {
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
  margin-top: 4px;
}

.funnel-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 20px 0;
}

.import-actions {
  border-top: 1px solid #f1f5f9;
  padding-top: 14px;
  margin-top: 8px;
}

.import-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}
</style>
