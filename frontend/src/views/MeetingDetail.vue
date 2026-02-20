<template>
  <div v-loading="loading" class="meeting-detail">
    <div v-if="meeting" class="detail-container">
      <!-- Header -->
      <div class="detail-header">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>

      <!-- Meeting Info Card -->
      <div class="section-card meeting-info-card">
        <div class="meeting-header">
          <div class="meeting-title-section">
            <h2>{{ meeting.title }}</h2>
            <el-tag :type="getStatusType(meeting.status)">
              {{ getStatusText(meeting.status) }}
            </el-tag>
          </div>
          <el-button
            v-if="isAdmin"
            type="primary"
            @click="editMeeting"
          >
            <el-icon><Edit /></el-icon>
            编辑会议
          </el-button>
        </div>

        <div v-if="meeting.description" class="meeting-description">
          {{ meeting.description }}
        </div>

        <el-row :gutter="16" class="meeting-meta">
          <el-col :span="8">
            <div class="meta-card">
              <el-icon class="meta-icon"><Calendar /></el-icon>
              <div class="meta-content">
                <div class="meta-label">会议时间</div>
                <div class="meta-value">{{ formatDateTime(meeting.scheduled_at) }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="meta-card">
              <el-icon class="meta-icon"><Clock /></el-icon>
              <div class="meta-content">
                <div class="meta-label">会议时长</div>
                <div class="meta-value">{{ meeting.duration }} 分钟</div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="meta-card">
              <el-icon class="meta-icon"><Location /></el-icon>
              <div class="meta-content">
                <div class="meta-label">会议地点</div>
                <div class="meta-value">
                  {{ meeting.location_type === 'online' ? '线上会议' : meeting.location || '未设置' }}
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <div v-if="meeting.committee_name" class="committee-info">
          <span class="info-label">所属委员会：</span>
          <el-link type="primary" @click="$router.push(`/committees/${meeting.committee_id}`)">
            {{ meeting.committee_name }}
          </el-link>
        </div>
      </div>

      <!-- Agenda Section -->
      <el-card v-if="meeting.agenda" class="section-card">
        <template #header>
          <span class="section-title">会议议程</span>
        </template>
        <div class="agenda-content" v-html="formatAgenda(meeting.agenda)"></div>
      </el-card>

      <!-- Minutes Section -->
      <el-card class="section-card">
        <template #header>
          <div class="section-header">
            <span class="section-title">会议纪要</span>
            <el-button
              v-if="isAdmin && !editingMinutes"
              type="primary"
              size="small"
              @click="startEditMinutes"
            >
              <el-icon><Edit /></el-icon>
              {{ meeting.minutes ? '编辑纪要' : '添加纪要' }}
            </el-button>
          </div>
        </template>

        <div v-if="!editingMinutes">
          <div v-if="meeting.minutes" class="minutes-content" v-html="formatMinutes(meeting.minutes)"></div>
          <el-empty v-else description="暂无会议纪要" :image-size="80" />
        </div>

        <div v-else>
          <el-input
            v-model="minutesForm.content"
            type="textarea"
            :rows="15"
            placeholder="输入会议纪要内容，支持Markdown格式"
          />
          <div class="minutes-actions">
            <el-button @click="cancelEditMinutes">取消</el-button>
            <el-button type="primary" :loading="savingMinutes" @click="saveMinutes">
              保存
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- Participants Section -->
      <el-card v-if="isAdmin" class="section-card">
        <template #header>
          <div class="section-header">
            <span class="section-title">会议参与者</span>
            <div class="header-actions">
              <el-button
                size="small"
                @click="showImportDialog = true"
                :disabled="!meeting.committee_id"
              >
                <el-icon><Download /></el-icon>
                从委员会名单导入
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="showAddParticipantDialog = true"
              >
                <el-icon><Plus /></el-icon>
                添加参与者
              </el-button>
            </div>
          </div>
        </template>

        <el-table :data="participants" v-loading="loadingParticipants">
          <el-table-column label="姓名" prop="name" />
          <el-table-column label="邮箱" prop="email" />
          <el-table-column label="来源" prop="source" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="row.source === 'committee' ? 'success' : ''">
                {{ row.source === 'committee' ? '理事会' : '手动添加' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-popconfirm
                title="确定删除此参与者吗？"
                @confirm="deleteParticipant(row.id)"
              >
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="participants.length === 0" description="暂无参与者" :image-size="80" />

        <!-- Send Calendar Invite Button -->
        <div v-if="participants.length > 0" class="send-calendar-section">
          <el-button
            type="success"
            :loading="sendingCalendar"
            @click="sendCalendarInvite"
          >
            <el-icon><Message /></el-icon>
            发送日历邀请（全部参与者）
          </el-button>
          <span class="hint-text">将向所有参与者发送包含日历文件的邮件邀请</span>
        </div>
      </el-card>

      <!-- Reminders Section -->
      <el-card v-if="isAdmin" class="section-card">
        <template #header>
          <div class="section-header">
            <span class="section-title">会议提醒</span>
            <el-button
              type="primary"
              size="small"
              @click="showReminderDialog = true"
            >
              <el-icon><Plus /></el-icon>
              创建提醒
            </el-button>
          </div>
        </template>

        <el-table :data="reminders" v-loading="loadingReminders">
          <el-table-column label="提醒类型" prop="reminder_type">
            <template #default="{ row }">
              {{ getReminderTypeText(row.reminder_type) }}
            </template>
          </el-table-column>
          <el-table-column label="发送时间" prop="scheduled_at">
            <template #default="{ row }">
              {{ formatDateTime(row.scheduled_at) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="status" width="180">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-tag :type="row.status === 'sent' ? 'success' : row.status === 'failed' ? 'danger' : ''">
                  {{ row.status === 'sent' ? '已发送' : row.status === 'failed' ? '失败' : '待发送' }}
                </el-tag>
                <el-tooltip v-if="row.status === 'failed' && row.error_message" placement="top" :content="row.error_message">
                  <el-icon color="#f56c6c" style="cursor: help;"><Warning /></el-icon>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="发送渠道" prop="notification_channels">
            <template #default="{ row }">
              {{ row.notification_channels.join(', ') || '未设置' }}
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="reminders.length === 0" description="暂无提醒" :image-size="80" />
      </el-card>
    </div>

    <!-- Reminder Dialog -->
    <el-dialog v-model="showReminderDialog" title="创建会议提醒" width="400px">
      <el-form label-width="100px">
        <el-form-item label="提醒类型">
          <el-select v-model="reminderType" placeholder="选择提醒类型" style="width: 100%">
            <el-option label="会前准备" value="preparation" />
            <el-option label="提前一周" value="one_week" />
            <el-option label="提前三天" value="three_days" />
            <el-option label="提前一天" value="one_day" />
            <el-option label="提前两小时" value="two_hours" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showReminderDialog = false">取消</el-button>
        <el-button type="primary" :loading="creatingReminder" @click="createReminder">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- Add Participant Dialog -->
    <el-dialog v-model="showAddParticipantDialog" title="添加参与者" width="400px">
      <el-form label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="participantForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="participantForm.email" type="email" placeholder="请输入邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddParticipantDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingParticipant" @click="addParticipant">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- Import Participants Dialog -->
    <el-dialog v-model="showImportDialog" title="从委员会名单导入参与者" width="450px">
      <el-alert
        title="导入说明"
        type="info"
        :closable="false"
        show-icon
      >
        <p>将从此会议所属的委员会中导入所有活跃成员（仅导入有邮箱的成员）</p>
        <p>已存在的参与者将自动跳过</p>
      </el-alert>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="importFromCommittee">
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Calendar,
  Clock,
  Location,
  Plus,
  Download,
  Message,
  Warning
} from '@element-plus/icons-vue'
import {
  getMeeting,
  updateMeetingMinutes,
  listMeetingReminders,
  createMeetingReminder,
  listMeetingParticipants,
  addMeetingParticipant,
  deleteMeetingParticipant,
  importParticipantsFromCommittee,
  type MeetingDetail,
  type MeetingParticipant,
  type MeetingReminder
} from '@/api/governance'
import { useUserStore } from '@/stores/user'
import { computed } from 'vue'

const route = useRoute()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.isCommunityAdmin)

const loading = ref(false)
const loadingReminders = ref(false)
const savingMinutes = ref(false)
const creatingReminder = ref(false)

const meeting = ref<MeetingDetail | null>(null)
const reminders = ref<MeetingReminder[]>([])

const editingMinutes = ref(false)
const minutesForm = ref({
  content: ''
})

const showReminderDialog = ref(false)
const reminderType = ref('one_day')

// Participants
const participants = ref<MeetingParticipant[]>([])
const loadingParticipants = ref(false)
const showAddParticipantDialog = ref(false)
const showImportDialog = ref(false)
const addingParticipant = ref(false)
const importing = ref(false)
const sendingCalendar = ref(false)
const participantForm = ref({
  name: '',
  email: ''
})

onMounted(() => {
  loadMeeting()
  if (isAdmin.value) {
    loadReminders()
    loadParticipants()
  }
})

async function loadMeeting() {
  const id = parseInt(route.params.id as string)
  if (isNaN(id)) return

  loading.value = true
  try {
    meeting.value = await getMeeting(id)
  } catch (error: any) {
    ElMessage.error(error.message || '加载会议详情失败')
  } finally {
    loading.value = false
  }
}

async function loadReminders() {
  const id = parseInt(route.params.id as string)
  if (isNaN(id)) return

  loadingReminders.value = true
  try {
    reminders.value = await listMeetingReminders(id)
  } catch (error: any) {
    ElMessage.error(error.message || '加载提醒失败')
  } finally {
    loadingReminders.value = false
  }
}

function editMeeting() {
  // Navigate to calendar with edit mode
  // Or implement inline edit
  ElMessage.info('请在日历页面编辑会议')
}

function startEditMinutes() {
  minutesForm.value.content = meeting.value?.minutes || ''
  editingMinutes.value = true
}

function cancelEditMinutes() {
  editingMinutes.value = false
  minutesForm.value.content = ''
}

async function saveMinutes() {
  if (!meeting.value) return

  savingMinutes.value = true
  try {
    const updated = await updateMeetingMinutes(meeting.value.id, minutesForm.value.content)
    meeting.value.minutes = updated.minutes
    editingMinutes.value = false
    ElMessage.success('保存成功')
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    savingMinutes.value = false
  }
}

async function createReminder() {
  if (!meeting.value) return

  creatingReminder.value = true
  try {
    await createMeetingReminder(meeting.value.id, reminderType.value)
    ElMessage.success('创建成功')
    showReminderDialog.value = false
    loadReminders()
  } catch (error: any) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    creatingReminder.value = false
  }
}

// ── Participants Functions ──────────────────────────────────────────
async function loadParticipants() {
  if (!meeting.value) return
  
  loadingParticipants.value = true
  try {
    participants.value = await listMeetingParticipants(meeting.value.id)
  } catch (error: any) {
    ElMessage.error('加载参与者列表失败')
  } finally {
    loadingParticipants.value = false
  }
}

async function addParticipant() {
  if (!meeting.value || !participantForm.value.name || !participantForm.value.email) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  addingParticipant.value = true
  try {
    await addMeetingParticipant(meeting.value.id, participantForm.value)
    ElMessage.success('添加成功')
    showAddParticipantDialog.value = false
    participantForm.value = { name: '', email: '' }
    loadParticipants()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '添加失败')
  } finally {
    addingParticipant.value = false
  }
}

async function deleteParticipant(participantId: number) {
  if (!meeting.value) return
  
  try {
    await deleteMeetingParticipant(meeting.value.id, participantId)
    ElMessage.success('删除成功')
    loadParticipants()
  } catch (error: any) {
    ElMessage.error('删除失败')
  }
}

async function importFromCommittee() {
  if (!meeting.value) return
  
  importing.value = true
  try {
    const result = await importParticipantsFromCommittee(meeting.value.id)
    ElMessage.success(`导入成功！共导入 ${result.added_count} 人，跳过 ${result.skipped_count} 人`)
    showImportDialog.value = false
    loadParticipants()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

async function sendCalendarInvite() {
  if (!meeting.value || participants.value.length === 0) return
  
  sendingCalendar.value = true
  try {
    // Create an immediate reminder to send calendar invites
    await createMeetingReminder(meeting.value.id, 'immediate')
    ElMessage.success('日历邀请已发送！')
    loadReminders()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '发送失败')
  } finally {
    sendingCalendar.value = false
  }
}

function formatDateTime(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatAgenda(agenda: string) {
  // Simple newline to <br> conversion
  return agenda.replace(/\n/g, '<br>')
}

function formatMinutes(minutes: string) {
  // Simple newline to <br> conversion
  // TODO: Add markdown support
  return minutes.replace(/\n/g, '<br>')
}

function getStatusType(status: string) {
  const map: Record<string, any> = {
    scheduled: 'primary',
    in_progress: 'success',
    completed: 'info',
    cancelled: 'danger'
  }
  return map[status] || ''
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    scheduled: '已安排',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status
}

function getReminderTypeText(type: string) {
  const map: Record<string, string> = {
    preparation: '会前准备',
    one_week: '提前一周',
    three_days: '提前三天',
    one_day: '提前一天',
    two_hours: '提前两小时'
  }
  return map[type] || type
}
</script>

<style scoped>
.meeting-detail {
  padding: 24px;
}

.detail-header {
  margin-bottom: 16px;
}

.meeting-info-card {
  margin-bottom: 24px;
}

.meeting-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.meeting-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meeting-title-section h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.meeting-description {
  color: var(--el-text-color-regular);
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.meeting-meta {
  margin-bottom: 16px;
}

.meta-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.meta-icon {
  font-size: 24px;
  color: #0095ff;
}

.meta-content {
  flex: 1;
}

.meta-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.meta-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.committee-info {
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.info-label {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-right: 8px;
}

.section-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
}

.agenda-content,
.minutes-content {
  line-height: 1.8;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
}

.minutes-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.send-calendar-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  gap: 12px;
}

.hint-text {
  color: #909399;
  font-size: 12px;
}
</style>
