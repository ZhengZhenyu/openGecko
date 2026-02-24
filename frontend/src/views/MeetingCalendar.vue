<template>
  <div class="meeting-calendar">
    <!-- Page Header -->
    <div class="page-title-row">
      <div class="page-title">
        <h2>会议日历</h2>
        <p class="subtitle">查看和管理委员会会议</p>
      </div>
      <el-button v-if="isAdmin" type="primary" :icon="Plus" @click="showCreateDialog = true">
        创建会议
      </el-button>
    </div>

    <!-- 社区未选择提示 -->
    <el-empty
      v-if="!communityStore.currentCommunityId"
      description="请先在顶部选择一个社区"
      :image-size="120"
    />

    <template v-else>
      <!-- Filter Bar -->
      <div class="filter-bar">
        <el-select
          v-model="selectedCommittee"
          placeholder="全部委员会"
          clearable
          style="width: 180px"
          @change="loadMeetings"
        >
          <el-option
            v-for="committee in committees"
            :key="committee.id"
            :label="committee.name"
            :value="committee.id"
          />
        </el-select>
        <el-radio-group v-model="viewMode" class="view-toggle">
          <el-radio-button value="month">月视图</el-radio-button>
          <el-radio-button value="list">列表视图</el-radio-button>
        </el-radio-group>
        <span class="meeting-count">共 {{ meetings.length }} 场会议</span>
      </div>

      <!-- Calendar View (FullCalendar) -->
      <div v-if="viewMode === 'month'" v-loading="loading" class="section-card calendar-card">
        <FullCalendar ref="calendarRef" :options="calendarOptions" class="fc-wrapper" />
      </div>

      <!-- List View -->
      <div v-else v-loading="loading" class="section-card list-card">
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
                <span class="status-badge" :class="`status-${meeting.status}`">
                  {{ getStatusText(meeting.status) }}
                </span>
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
                  <template v-if="meeting.location_type === 'online'">线上会议</template>
                  <template v-else-if="meeting.location_type === 'hybrid'">线上线下混合</template>
                  <template v-else>{{ meeting.location }}</template>
                </span>
                <span v-if="(meeting as any).assignee_ids?.length > 0">
                  <el-icon><User /></el-icon>
                  {{ (meeting as any).assignee_ids.length }} 位责任人
                </span>
              </div>
              <div v-if="meeting.description" class="meeting-description">
                {{ meeting.description }}
              </div>
            </div>
            <div v-if="isAdmin" class="meeting-actions" @click.stop>
              <el-button text size="small" @click="editMeeting(meeting)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button text size="small" type="danger" @click="confirmDelete(meeting)">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </div>
          </div>

          <el-empty v-if="sortedMeetings.length === 0" description="暂无会议" />
        </div>
      </div>

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
          <el-form-item label="会议描述">
            <el-input v-model="form.description" type="textarea" :rows="3" placeholder="简要描述会议内容" />
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
          <el-form-item label="会议时长">
            <el-input-number v-model="form.duration" :min="15" :max="480" :step="15" style="width: 160px" />
            <span class="form-tip">分钟</span>
          </el-form-item>
          <el-form-item label="会议地点">
            <el-radio-group v-model="form.location_type">
              <el-radio value="online">线上会议</el-radio>
              <el-radio value="offline">线下会议</el-radio>
              <el-radio value="hybrid">线上线下混合</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item
            v-if="form.location_type === 'online' || form.location_type === 'hybrid'"
            label="会议链接"
          >
            <el-input v-model="form.online_url" placeholder="Zoom / 腾讯会议链接" />
          </el-form-item>
          <el-form-item
            v-if="form.location_type === 'offline' || form.location_type === 'hybrid'"
            label="线下地址"
          >
            <el-input v-model="form.location" placeholder="输入线下会议地址" />
          </el-form-item>
          <el-form-item label="会议议程">
            <el-input v-model="form.agenda" type="textarea" :rows="5" placeholder="输入会议议程" />
          </el-form-item>
          <el-form-item label="提前提醒">
            <el-select v-model="form.reminder_before_hours" style="width: 100%">
              <el-option label="不提醒" :value="0" />
              <el-option label="提前2小时" :value="2" />
              <el-option label="提前24小时" :value="24" />
              <el-option label="提前48小时" :value="48" />
              <el-option label="提前1周" :value="168" />
            </el-select>
          </el-form-item>
          <el-form-item label="责任人">
            <el-select v-model="form.assignee_ids" multiple filterable placeholder="选择责任人（默认为创建者）" style="width: 100%">
              <el-option
                v-for="u in communityMembers"
                :key="u.id"
                :label="`${u.username} (${u.email})`"
                :value="u.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item v-if="editingMeeting" label="状态">
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Clock, Location, Edit, Delete, UserFilled, User } from '@element-plus/icons-vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { CalendarOptions, EventClickArg } from '@fullcalendar/core'
import {
  listCommittees,
  listMeetings,
  createMeeting,
  updateMeeting,
  deleteMeeting,
  type Committee,
  type Meeting,
  type MeetingCreate,
  type MeetingUpdate,
} from '@/api/governance'
import { getCommunityUsers, type CommunityUser } from '@/api/community'
import { useUserStore } from '@/stores/user'
import { useCommunityStore } from '@/stores/community'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const communityStore = useCommunityStore()
const authStore = useAuthStore()

const isAdmin = computed(() => userStore.isCommunityAdmin)

const loading = ref(false)
const submitting = ref(false)
const viewMode = ref<'month' | 'list'>('list')
const selectedCommittee = ref<number | undefined>()
const calendarRef = ref()

const committees = ref<Committee[]>([])
const meetings = ref<Meeting[]>([])
const communityMembers = ref<CommunityUser[]>([])

const showCreateDialog = ref(false)
const editingMeeting = ref<Meeting | null>(null)
const formRef = ref<FormInstance>()

const statusColorMap: Record<string, string> = {
  scheduled: '#0095ff',
  in_progress: '#22c55e',
  completed: '#94a3b8',
  cancelled: '#ef4444',
}

interface MeetingForm {
  committee_id?: number
  title: string
  description?: string
  scheduled_at: string
  duration: number
  location_type: string
  location?: string
  online_url?: string
  agenda?: string
  reminder_before_hours: number
  status?: string
  assignee_ids: number[]
}

const form = ref<MeetingForm>({
  committee_id: undefined,
  title: '',
  description: '',
  scheduled_at: '',
  duration: 120,
  location_type: 'online',
  location: '',
  online_url: '',
  agenda: '',
  reminder_before_hours: 24,
  status: 'scheduled',
  assignee_ids: [],
})

const rules: FormRules = {
  committee_id: [{ required: true, message: '请选择委员会', trigger: 'change' }],
  title: [{ required: true, message: '请输入会议标题', trigger: 'blur' }],
  scheduled_at: [{ required: true, message: '请选择会议时间', trigger: 'change' }],
}

const sortedMeetings = computed(() =>
  [...meetings.value].sort(
    (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime(),
  ),
)

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-cn',
  height: 'auto',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  buttonText: { today: '今天' },
  dayMaxEvents: 3,
  events: meetings.value.map(m => ({
    id: String(m.id),
    title: `${formatTime(m.scheduled_at)} ${m.title}`,
    start: m.scheduled_at,
    color: statusColorMap[m.status] || '#94a3b8',
  })),
  eventClick: (info: EventClickArg) => {
    router.push(`/meetings/${info.event.id}`)
  },
}))

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadCommittees()
    loadMeetings()
    loadCommunityMembers()
  }
  if (route.query.action === 'create') {
    showCreateDialog.value = true
    if (authStore.user?.id) {
      form.value.assignee_ids = [authStore.user.id]
    }
  }
})

watch(
  () => communityStore.currentCommunityId,
  newId => {
    if (newId) {
      loadCommittees()
      loadMeetings()
      loadCommunityMembers()
    }
  },
)

async function loadCommunityMembers() {
  const communityId = communityStore.currentCommunityId
  if (!communityId) return
  try {
    communityMembers.value = await getCommunityUsers(communityId)
  } catch {
    // ignore
  }
}

async function loadCommittees() {
  try {
    committees.value = await listCommittees()
  } catch (e: any) {
    ElMessage.error(e.message || '加载委员会失败')
  }
}

async function loadMeetings() {
  loading.value = true
  try {
    const params: any = { limit: 200 }
    if (selectedCommittee.value) params.committee_id = selectedCommittee.value
    meetings.value = await listMeetings(params)
  } catch (e: any) {
    ElMessage.error(e.message || '加载会议失败')
  } finally {
    loading.value = false
  }
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
    online_url: meeting.online_url,
    agenda: '',
    reminder_before_hours: 24,
    status: meeting.status,
    assignee_ids: (meeting as any).assignee_ids || [],
  }
  showCreateDialog.value = true
}

async function confirmDelete(meeting: Meeting) {
  try {
    await ElMessageBox.confirm(
      `确定要删除会议「${meeting.title}」吗？`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await deleteMeeting(meeting.id)
    ElMessage.success('删除成功')
    loadMeetings()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.message || '删除失败')
  }
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async valid => {
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
          online_url: form.value.online_url,
          status: form.value.status,
          agenda: form.value.agenda,
          reminder_before_hours: form.value.reminder_before_hours,
          assignee_ids: form.value.assignee_ids,
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
          online_url: form.value.online_url,
          agenda: form.value.agenda,
          reminder_before_hours: form.value.reminder_before_hours,
          assignee_ids: form.value.assignee_ids,
        }
        await createMeeting(createData)
        ElMessage.success('创建成功')
      }
      showCreateDialog.value = false
      editingMeeting.value = null
      formRef.value?.resetFields()
      loadMeetings()
    } catch (e: any) {
      ElMessage.error(e.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
    minute: '2-digit',
  })
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    scheduled: '已安排',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[status] || status
}

function getCommitteeName(committeeId: number) {
  return committees.value.find(c => c.id === committeeId)?.name || '未知委员会'
}
</script>

<style scoped>
.meeting-calendar {
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
  max-width: 1440px;
  margin: 0 auto;
}

/* ── Page Header ── */
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

/* ── Filter Bar ── */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.meeting-count {
  font-size: 13px;
  color: var(--text-muted);
  margin-left: 4px;
}

/* ── Section Card ── */
.section-card {
  background: #ffffff;
  border-radius: var(--radius);
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

/* ── FullCalendar overrides ── */
.fc-wrapper {
  --fc-border-color: #f1f5f9;
  --fc-today-bg-color: rgba(0, 149, 255, 0.06);
  --fc-event-border-color: transparent;
  --fc-page-bg-color: #ffffff;
  --fc-neutral-bg-color: #f8fafc;
}

:deep(.fc .fc-toolbar.fc-header-toolbar) {
  margin-bottom: 20px;
}

:deep(.fc .fc-toolbar-title) {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

:deep(.fc .fc-button-primary) {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  border-radius: 8px;
  padding: 4px 12px;
  box-shadow: none;
  transition: all 0.15s;
}

:deep(.fc .fc-button-primary:hover) {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: var(--text-primary);
}

:deep(.fc .fc-button-primary:not(:disabled):active),
:deep(.fc .fc-button-primary:not(:disabled).fc-button-active) {
  background: var(--blue);
  border-color: var(--blue);
  color: #fff;
  box-shadow: none;
}

:deep(.fc .fc-button-group) {
  gap: 4px;
}

:deep(.fc .fc-col-header-cell) {
  background: #f8fafc;
  padding: 10px 0;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-color: #f1f5f9;
}

:deep(.fc .fc-daygrid-day) {
  transition: background 0.12s;
}

:deep(.fc .fc-daygrid-day:hover) {
  background: #fafbfc;
}

:deep(.fc .fc-daygrid-day-number) {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 6px 10px;
}

:deep(.fc .fc-day-today .fc-daygrid-day-number) {
  background: var(--blue);
  color: #fff;
  border-radius: 14px;
  padding: 2px 8px;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0, 149, 255, 0.35);
}

:deep(.fc .fc-daygrid-event) {
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  padding: 1px 5px;
  border: none;
  cursor: pointer;
  transition: opacity 0.12s, transform 0.12s;
}

:deep(.fc .fc-daygrid-event:hover) {
  opacity: 0.85;
  transform: translateY(-1px);
}

:deep(.fc .fc-more-link) {
  font-size: 11px;
  color: var(--blue);
  font-weight: 600;
}

:deep(.fc td),
:deep(.fc th) {
  border-color: #f1f5f9;
}

/* ── List View ── */
.meeting-list-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 8px;
}

.meeting-list-item:last-child {
  border-bottom: none;
}

.meeting-list-item:hover {
  background: #f8fafc;
}

.meeting-date-block {
  flex-shrink: 0;
  width: 52px;
  text-align: center;
  padding: 8px 6px;
  background: rgba(0, 149, 255, 0.07);
  border-radius: 10px;
  border: 1px solid rgba(0, 149, 255, 0.15);
}

.date-month {
  font-size: 11px;
  font-weight: 600;
  color: var(--blue);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.date-day {
  font-size: 22px;
  font-weight: 700;
  color: var(--blue);
  line-height: 1.2;
}

.meeting-content {
  flex: 1;
  min-width: 0;
}

.meeting-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  gap: 12px;
}

.meeting-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Status Badge */
.status-badge {
  flex-shrink: 0;
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.status-scheduled {
  background: rgba(0, 149, 255, 0.1);
  color: var(--blue);
}

.status-in_progress {
  background: rgba(34, 197, 94, 0.1);
  color: #15803d;
}

.status-completed {
  background: #f1f5f9;
  color: var(--text-muted);
}

.status-cancelled {
  background: #fef2f2;
  color: var(--red);
}

.meeting-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.meeting-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meeting-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.meeting-actions {
  flex-shrink: 0;
  display: flex;
  gap: 4px;
  align-items: flex-start;
}

/* Form */
.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

/* Element Plus overrides */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-dialog) {
  border-radius: var(--radius);
}

/* Responsive */
@media (max-width: 1200px) {
  .meeting-calendar { padding: 28px 24px; }
}

@media (max-width: 768px) {
  .meeting-calendar { padding: 20px 16px; }
  .page-title-row { flex-direction: column; gap: 16px; }
  .filter-bar { gap: 8px; }
}
</style>
