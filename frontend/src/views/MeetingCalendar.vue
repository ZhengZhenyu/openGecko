<template>
  <div class="meeting-calendar">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-header">
        <div class="header-title">
          <h2>会议日历</h2>
          <p>查看和管理委员会会议</p>
        </div>
        <el-button
          v-if="isAdmin"
          type="primary"
          @click="showCreateDialog = true"
        >
          <el-icon><Plus /></el-icon>
          创建会议
        </el-button>
      </div>

      <div class="filter-bar">
        <el-select
          v-model="selectedCommittee"
          placeholder="选择委员会"
          clearable
          style="width: 200px"
          @change="loadMeetings"
        >
          <el-option
            v-for="committee in committees"
            :key="committee.id"
            :label="committee.name"
            :value="committee.id"
          />
        </el-select>

        <el-radio-group v-model="viewMode" @change="handleViewModeChange">
          <el-radio-button value="month">月视图</el-radio-button>
          <el-radio-button value="list">列表视图</el-radio-button>
        </el-radio-group>
      </div>

      <!-- Calendar View -->
      <el-card v-if="viewMode === 'month'" v-loading="loading" class="calendar-card">
        <el-calendar v-model="currentDate">
          <template #date-cell="{ data }">
            <div class="calendar-day">
              <div class="day-number">{{ data.day.split('-').slice(-1)[0] }}</div>
              <div
                v-for="meeting in getMeetingsForDate(data.day)"
                :key="meeting.id"
                class="meeting-item"
                :class="`status-${meeting.status}`"
                @click="goToMeetingDetail(meeting.id)"
              >
                <div class="meeting-time">
                  {{ formatTime(meeting.scheduled_at) }}
                </div>
                <div class="meeting-committee">{{ getCommitteeName(meeting.committee_id) }}</div>
                <div class="meeting-title">{{ meeting.title }}</div>
              </div>
            </div>
          </template>
        </el-calendar>
      </el-card>

      <!-- List View -->
      <el-card v-else v-loading="loading" class="list-card">
        <div class="meeting-list">
          <div
            v-for="meeting in sortedMeetings"
            :key="meeting.id"
            class="meeting-list-item"
            @click="goToMeetingDetail(meeting.id)"
          >
            <div class="meeting-date-block">
              <div class="date-month">{{ formatMonth(meeting.scheduled_at) }}</div>
              <div class="date-day">{{ formatDay(meeting.scheduled_at) }}</div>
            </div>
            <div class="meeting-content">
              <div class="meeting-header">
                <h4>{{ meeting.title }}</h4>
                <el-tag :type="getStatusType(meeting.status)" size="small">
                  {{ getStatusText(meeting.status) }}
                </el-tag>
              </div>
              <div class="meeting-meta">
                <span>
                  <el-icon><UserFilled /></el-icon>
                  {{ getCommitteeName(meeting.committee_id) }}
                </span>
                <span>
                  <el-icon><Clock /></el-icon>
                  {{ formatDateTime(meeting.scheduled_at) }} · {{ meeting.duration }}分钟
                </span>
                <span v-if="meeting.location_type">
                  <el-icon><Location /></el-icon>
                  {{ meeting.location_type === 'online' ? '线上会议' : meeting.location }}
                </span>
              </div>
              <div v-if="meeting.description" class="meeting-description">
                {{ meeting.description }}
              </div>
            </div>
            <div v-if="isAdmin" class="meeting-actions" @click.stop>
              <el-button type="primary" link size="small" @click="editMeeting(meeting)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button type="danger" link size="small" @click="confirmDelete(meeting)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>

          <el-empty v-if="sortedMeetings.length === 0" description="暂无会议" />
        </div>
      </el-card>

      <!-- Create/Edit Dialog -->
      <el-dialog
        v-model="showCreateDialog"
        :title="editingMeeting ? '编辑会议' : '创建会议'"
        width="600px"
      >
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
        >
          <el-form-item label="委员会" prop="committee_id">
            <el-select v-model="form.committee_id" placeholder="选择委员会" style="width: 100%">
              <el-option
                v-for="committee in committees"
                :key="committee.id"
                :label="committee.name"
                :value="committee.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="会议标题" prop="title">
            <el-input v-model="form.title" placeholder="如：2024年第一次技术委员会会议" />
          </el-form-item>

          <el-form-item label="会议描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="简要描述会议内容"
            />
          </el-form-item>

          <el-form-item label="会议时间" prop="scheduled_at">
            <el-date-picker
              v-model="form.scheduled_at"
              type="datetime"
              placeholder="选择日期时间"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="会议时长" prop="duration">
            <el-input-number
              v-model="form.duration"
              :min="15"
              :max="480"
              :step="15"
              style="width: 100%"
            />
            <span class="form-tip">分钟</span>
          </el-form-item>

          <el-form-item label="会议地点" prop="location_type">
            <el-radio-group v-model="form.location_type">
              <el-radio value="online">线上会议</el-radio>
              <el-radio value="offline">线下会议</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.location_type === 'offline'" label="具体地址" prop="location">
            <el-input v-model="form.location" placeholder="输入会议地址" />
          </el-form-item>

          <el-form-item v-if="form.location_type === 'online'" label="会议链接" prop="location">
            <el-input v-model="form.location" placeholder="输入会议链接或ID" />
          </el-form-item>

          <el-form-item label="会议议程" prop="agenda">
            <el-input
              v-model="form.agenda"
              type="textarea"
              :rows="5"
              placeholder="输入会议议程"
            />
          </el-form-item>

          <el-form-item label="提前提醒" prop="reminder_before_hours">
            <el-select v-model="form.reminder_before_hours" style="width: 100%">
              <el-option label="不提醒" :value="0" />
              <el-option label="提前2小时" :value="2" />
              <el-option label="提前24小时" :value="24" />
              <el-option label="提前48小时" :value="48" />
              <el-option label="提前1周" :value="168" />
            </el-select>
          </el-form-item>

          <el-form-item v-if="editingMeeting" label="状态" prop="status">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="已安排" value="scheduled" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            {{ editingMeeting ? '更新' : '创建' }}
          </el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Clock,
  Location,
  Edit,
  Delete,
  UserFilled
} from '@element-plus/icons-vue'
import {
  listCommittees,
  listMeetings,
  createMeeting,
  updateMeeting,
  deleteMeeting,
  type Committee,
  type Meeting,
  type MeetingCreate,
  type MeetingUpdate
} from '@/api/governance'
import { useUserStore } from '@/stores/user'
import { useCommunityStore } from '@/stores/community'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const communityStore = useCommunityStore()

const isAdmin = computed(() => userStore.isCommunityAdmin)

const loading = ref(false)
const submitting = ref(false)
const viewMode = ref<'month' | 'list'>('list')
const currentDate = ref(new Date())
const selectedCommittee = ref<number | undefined>()

const committees = ref<Committee[]>([])
const meetings = ref<Meeting[]>([])

const showCreateDialog = ref(false)
const editingMeeting = ref<Meeting | null>(null)
const formRef = ref<FormInstance>()

interface MeetingForm {
  committee_id?: number
  title: string
  description?: string
  scheduled_at: string
  duration: number
  location_type: string
  location?: string
  agenda?: string
  reminder_before_hours: number
  status?: string
}

const form = ref<MeetingForm>({
  committee_id: undefined,
  title: '',
  description: '',
  scheduled_at: '',
  duration: 120,
  location_type: 'online',
  location: '',
  agenda: '',
  reminder_before_hours: 24,
  status: 'scheduled'
})

const rules: FormRules = {
  committee_id: [{ required: true, message: '请选择委员会', trigger: 'change' }],
  title: [
    { required: true, message: '请输入会议标题', trigger: 'blur' },
    { min: 1, max: 500, message: '标题长度在1-500个字符', trigger: 'blur' }
  ],
  scheduled_at: [{ required: true, message: '请选择会议时间', trigger: 'change' }]
}

const sortedMeetings = computed(() => {
  return [...meetings.value].sort((a, b) => {
    return new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
  })
})

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadCommittees()
    loadMeetings()
  }

  if (route.query.action === 'create') {
    showCreateDialog.value = true
  }
})

// Watch for community changes
watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) {
      loadCommittees()
      loadMeetings()
    }
  }
)

async function loadCommittees() {
  try {
    committees.value = await listCommittees()
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会失败')
  }
}

async function loadMeetings() {
  loading.value = true
  try {
    const params: any = { limit: 200 }
    if (selectedCommittee.value) {
      params.committee_id = selectedCommittee.value
    }
    meetings.value = await listMeetings(params)
  } catch (error: any) {
    ElMessage.error(error.message || '加载会议失败')
  } finally {
    loading.value = false
  }
}

function getMeetingsForDate(dateStr: string) {
  return meetings.value.filter(meeting => {
    const meetingDate = new Date(meeting.scheduled_at).toISOString().split('T')[0]
    return meetingDate === dateStr
  })
}

function handleViewModeChange() {
  // Handle view mode change
}

function goToMeetingDetail(id: number) {
  router.push(`/meetings/${id}`)
}

function editMeeting(meeting: Meeting) {
  editingMeeting.value = meeting
  form.value = {
    committee_id: meeting.committee_id,
    title: meeting.title,
    description: meeting.description,
    scheduled_at: meeting.scheduled_at,
    duration: meeting.duration,
    location_type: meeting.location_type || 'online',
    location: meeting.location,
    agenda: '',
    reminder_before_hours: 24,
    status: meeting.status
  }
  showCreateDialog.value = true
}

async function confirmDelete(meeting: Meeting) {
  try {
    await ElMessageBox.confirm(
      `确定要删除会议"${meeting.title}"吗？`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    await deleteMeeting(meeting.id)
    ElMessage.success('删除成功')
    loadMeetings()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function submitForm() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (editingMeeting.value) {
        const updateData: MeetingUpdate = {
          title: form.value.title,
          description: form.value.description,
          scheduled_at: form.value.scheduled_at,
          duration: form.value.duration,
          location_type: form.value.location_type,
          location: form.value.location,
          status: form.value.status,
          agenda: form.value.agenda,
          reminder_before_hours: form.value.reminder_before_hours
        }
        await updateMeeting(editingMeeting.value.id, updateData)
        ElMessage.success('更新成功')
      } else {
        const createData: MeetingCreate = {
          committee_id: form.value.committee_id!,
          title: form.value.title,
          description: form.value.description,
          scheduled_at: form.value.scheduled_at,
          duration: form.value.duration,
          location_type: form.value.location_type,
          location: form.value.location,
          agenda: form.value.agenda,
          reminder_before_hours: form.value.reminder_before_hours
        }
        await createMeeting(createData)
        ElMessage.success('创建成功')
      }
      showCreateDialog.value = false
      editingMeeting.value = null
      formRef.value?.resetFields()
      loadMeetings()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatMonth(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short' })
}

function formatDay(dateStr: string) {
  return new Date(dateStr).getDate()
}

function formatDateTime(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

function getCommitteeName(committeeId: number) {
  const committee = committees.value.find(c => c.id === committeeId)
  return committee ? committee.name : '未知委员会'
}
</script>

<style scoped>
.meeting-calendar {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-title h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
}

.header-title p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.calendar-card {
  margin-bottom: 24px;
}

.calendar-day {
  min-height: 80px;
  padding: 4px;
}

.day-number {
  text-align: center;
  font-weight: 600;
  margin-bottom: 4px;
}

.meeting-item {
  font-size: 12px;
  padding: 2px 4px;
  margin-bottom: 2px;
  border-radius: 2px;
  cursor: pointer;
  border-left: 3px solid;
}

.meeting-item.status-scheduled {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.meeting-item.status-completed {
  background: var(--el-color-info-light-9);
  border-color: var(--el-color-info);
}

.meeting-item.status-cancelled {
  background: var(--el-color-danger-light-9);
  border-color: var(--el-color-danger);
}

.meeting-time {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.meeting-committee {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin: 1px 0;
}

.meeting-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-card {
  margin-bottom: 24px;
}

.meeting-list-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background 0.2s;
}

.meeting-list-item:hover {
  background: var(--el-fill-color-light);
}

.meeting-date-block {
  flex-shrink: 0;
  width: 60px;
  text-align: center;
  padding: 8px;
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
}

.date-month {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
}

.date-day {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.meeting-content {
  flex: 1;
}

.meeting-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.meeting-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.meeting-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.meeting-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meeting-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.meeting-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
