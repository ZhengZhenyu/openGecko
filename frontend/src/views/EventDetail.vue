<template>
  <div v-loading="loading" class="event-detail">
    <template v-if="event || isNewEvent">
      <!-- Page Header -->
      <div class="detail-header">
        <el-button link @click="$router.push('/events')">
          <el-icon><ArrowLeft /></el-icon>
          {{ isNewEvent ? '返回活动列表' : '返回活动列表' }}
        </el-button>
      </div>

      <!-- Event Info Card -->
      <div class="info-card">
        <div class="info-top">
          <div class="info-title-row">
            <h1 class="event-title">{{ isNewEvent ? '创建活动' : (isEditing ? editForm.title : event.title) }}</h1>
            <div v-if="!isNewEvent && event" class="info-badges">
              <el-tag :type="typeTagMap[event.event_type] ?? 'info'">{{ typeLabel[event.event_type] ?? event.event_type }}</el-tag>
              <el-tag :type="statusTagMap[event.status] ?? 'info'">{{ statusLabel[event.status] ?? event.status }}</el-tag>
            </div>
          </div>
          <div class="info-actions">
            <el-button v-if="!isEditing && !isNewEvent" size="small" @click="startEdit">编辑</el-button>
            <template v-else-if="isEditing || isNewEvent">
              <el-button size="small" @click="cancelEdit">取消</el-button>
              <el-button size="small" type="primary" :loading="saving" @click="saveEdit">保存</el-button>
            </template>
            <el-select
              v-if="!isNewEvent && event"
              v-model="event.status"
              size="small"
              style="width: 120px"
              @change="handleStatusChange"
            >
              <el-option v-for="(label, val) in statusLabel" :key="val" :label="label" :value="val" />
            </el-select>
          </div>
        </div>

        <div v-if="!isEditing && event" class="info-meta-grid">
          <div v-if="event.planned_at" class="meta-item">
            <el-icon><Calendar /></el-icon>
            <span>{{ formatDateTime(event.planned_at) }}</span>
            <span v-if="event.duration_minutes" class="meta-sub">（{{ event.duration_minutes }} 分钟）</span>
          </div>
          <div v-if="event.location" class="meta-item">
            <el-icon><Location /></el-icon>
            <span>{{ event.location }}</span>
          </div>
          <div v-if="event.online_url" class="meta-item">
            <el-icon><Link /></el-icon>
            <a :href="event.online_url" target="_blank">{{ event.online_url }}</a>
          </div>
        </div>

        <div v-else class="edit-form">
          <el-form :model="editForm" label-width="90px" size="small">
            <el-form-item label="活动名称">
              <el-input v-model="editForm.title" />
            </el-form-item>
            <el-form-item label="活动状态">
              <el-select v-model="editForm.status" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="策划中" value="planning" />
                <el-option label="进行中" value="ongoing" />
                <el-option label="已完成" value="completed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-form-item>
            <el-form-item label="计划时间">
              <el-date-picker v-model="editForm.planned_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
            </el-form-item>
            <el-form-item label="时长（分钟）">
              <el-input-number v-model="editForm.duration_minutes" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="地点">
              <el-input v-model="editForm.location" />
            </el-form-item>
            <el-form-item label="在线链接">
              <el-input v-model="editForm.online_url" />
            </el-form-item>
            <el-form-item label="简介">
              <el-input v-model="editForm.description" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </div>

        <p v-if="!isEditing && event && event.description" class="event-description">{{ event.description }}</p>
      </div>

      <!-- Tabs -->
      <el-tabs v-if="!isNewEvent" v-model="activeTab" class="detail-tabs">
        <!-- 清单 Tab -->
        <el-tab-pane label="执行清单" name="checklist">
          <div v-loading="checklistLoading" class="tab-content">
            <div v-if="checklistByPhase.pre.length || checklistByPhase.during.length || checklistByPhase.post.length">
              <div v-for="phase in phases" :key="phase.key" class="checklist-phase">
                <h4 class="phase-title">{{ phase.label }}</h4>
                <div v-if="checklistByPhase[phase.key].length === 0" class="phase-empty">本阶段无清单项</div>
                <div
                  v-for="item in checklistByPhase[phase.key]"
                  :key="item.id"
                  class="checklist-item"
                  :class="{ done: item.status === 'done' }"
                >
                  <el-checkbox
                    :model-value="item.status === 'done'"
                    @change="(v: boolean) => toggleChecklist(item, v)"
                  />
                  <span class="checklist-title">{{ item.title }}</span>
                  <el-tag v-if="item.status === 'done'" type="success" size="small">已完成</el-tag>
                  <el-tag v-else-if="item.status === 'in_progress'" type="warning" size="small">进行中</el-tag>
                </div>
              </div>
            </div>
            <div v-else class="tab-empty">暂无清单项（创建活动时选择模板可自动生成）</div>
          </div>
        </el-tab-pane>

        <!-- 人员 Tab -->
        <el-tab-pane label="人员分工" name="personnel">
          <div v-loading="personnelLoading" class="tab-content">
            <div class="tab-actions">
              <el-button size="small" type="primary" @click="showAddPersonnelDialog = true">
                <el-icon><Plus /></el-icon>添加人员
              </el-button>
            </div>
            <el-table :data="personnel" style="width: 100%">
              <el-table-column label="角色" prop="role" width="120" />
              <el-table-column label="角色说明" prop="role_label" width="140" />
              <el-table-column label="时间段" prop="time_slot" />
              <el-table-column label="确认状态" width="120">
                <template #default="{ row }">
                  <el-tag :type="confirmTagMap[row.confirmed] ?? 'info'" size="small">
                    {{ confirmLabel[row.confirmed] ?? row.confirmed }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="备注" prop="notes" />
              <el-table-column label="操作" width="140">
                <template #default="{ row }">
                  <template v-if="row.confirmed === 'pending'">
                    <el-button link type="primary" size="small" @click="handleConfirmPersonnel(row.id, 'confirmed')">确认</el-button>
                    <el-button link type="danger" size="small" @click="handleConfirmPersonnel(row.id, 'declined')">拒绝</el-button>
                  </template>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 任务规划 Tab (甘特图) -->
        <el-tab-pane label="任务规划" name="tasks">
          <div v-loading="tasksLoading" class="tab-content">
            <div class="tab-actions">
              <el-button size="small" type="primary" @click="showAddTaskDialog = true">
                <el-icon><Plus /></el-icon>添加任务
              </el-button>
            </div>

            <!-- Task list table -->
            <el-table :data="flatTasks" row-key="id" style="width: 100%; margin-bottom: 24px">
              <el-table-column label="任务名称" prop="title" min-width="180">
                <template #default="{ row }">
                  <span :style="{ paddingLeft: row.parent_task_id ? '20px' : '0' }">
                    {{ row.title }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="类型" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.task_type === 'milestone' ? 'warning' : ''" size="small">
                    {{ row.task_type === 'milestone' ? '里程碑' : '任务' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="阶段" width="90">
                <template #default="{ row }">{{ phaseLabel[row.phase] ?? row.phase }}</template>
              </el-table-column>
              <el-table-column label="开始" prop="start_date" width="110" />
              <el-table-column label="结束" prop="end_date" width="110" />
              <el-table-column label="进度" width="120">
                <template #default="{ row }">
                  <el-progress :percentage="row.progress" :stroke-width="6" />
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="taskStatusTagMap[row.status] ?? 'info'" size="small">
                    {{ taskStatusLabel[row.status] ?? row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button link type="danger" size="small" @click="handleDeleteTask(row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- Gantt Chart -->
            <div v-if="ganttTasks.length > 0" class="gantt-wrapper">
              <h4 class="gantt-title">甘特图</h4>
              <div ref="ganttEl" class="gantt-container" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 现场反馈 Tab -->
        <el-tab-pane label="现场反馈" name="feedback">
          <div v-loading="feedbackLoading" class="tab-content">
            <div class="tab-actions">
              <el-button size="small" type="primary" @click="showAddFeedbackDialog = true">
                <el-icon><Plus /></el-icon>记录反馈
              </el-button>
            </div>
            <div v-if="feedback.length === 0" class="tab-empty">暂无反馈记录</div>
            <div v-for="fb in feedback" :key="fb.id" class="feedback-card">
              <div class="feedback-header">
                <el-tag :type="feedbackTagMap[fb.category] ?? 'info'" size="small">
                  {{ feedbackCategoryLabel[fb.category] ?? fb.category }}
                </el-tag>
                <el-tag :type="fb.status === 'closed' ? 'success' : fb.status === 'in_progress' ? 'warning' : 'info'" size="small">
                  {{ feedbackStatusLabel[fb.status] ?? fb.status }}
                </el-tag>
                <span class="feedback-meta">{{ fb.raised_by || '匿名' }} · {{ formatDate(fb.created_at) }}</span>
                <div class="feedback-actions">
                  <el-button v-if="fb.status === 'open'" link type="primary" size="small" @click="handleUpdateFeedbackStatus(fb.id, 'in_progress')">处理中</el-button>
                  <el-button v-if="fb.status === 'in_progress'" link type="success" size="small" @click="handleUpdateFeedbackStatus(fb.id, 'closed')">关闭</el-button>
                  <el-button v-if="fb.status === 'closed'" link type="warning" size="small" @click="handleUpdateFeedbackStatus(fb.id, 'open')">重新打开</el-button>
                </div>
              </div>
              <p class="feedback-content">{{ fb.content }}</p>
              <div v-if="fb.issue_links.length > 0" class="issue-links">
                <a v-for="link in fb.issue_links" :key="link.id" :href="link.issue_url" target="_blank" class="issue-link">
                  {{ link.platform }}#{{ link.issue_number }} ({{ link.issue_status }})
                </a>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>

    <!-- Add Task Dialog -->
    <el-dialog v-model="showAddTaskDialog" title="添加任务" width="460px" destroy-on-close>
      <el-form :model="taskForm" label-width="80px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.title" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="taskForm.task_type" style="width: 100%">
            <el-option label="任务" value="task" />
            <el-option label="里程碑" value="milestone" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段">
          <el-select v-model="taskForm.phase" style="width: 100%">
            <el-option label="会前" value="pre" />
            <el-option label="会中" value="during" />
            <el-option label="会后" value="post" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="taskForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="taskForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTaskDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingTask" @click="handleAddTask">添加</el-button>
      </template>
    </el-dialog>

    <!-- Add Personnel Dialog -->
    <el-dialog v-model="showAddPersonnelDialog" title="添加人员" width="420px" destroy-on-close>
      <el-form :model="personnelForm" label-width="90px">
        <el-form-item label="角色" required>
          <el-input v-model="personnelForm.role" placeholder="如：主持人、演讲嘉宾" />
        </el-form-item>
        <el-form-item label="角色备注">
          <el-input v-model="personnelForm.role_label" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="personnelForm.assignee_type" style="width: 100%">
            <el-option label="内部成员" value="internal" />
            <el-option label="外部嘉宾" value="external" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间段">
          <el-input v-model="personnelForm.time_slot" placeholder="如：14:00-14:30" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="personnelForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPersonnelDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingPersonnel" @click="handleAddPersonnel">添加</el-button>
      </template>
    </el-dialog>

    <!-- Add Feedback Dialog -->
    <el-dialog v-model="showAddFeedbackDialog" title="记录反馈" width="420px" destroy-on-close>
      <el-form :model="feedbackForm" label-width="80px">
        <el-form-item label="类别">
          <el-select v-model="feedbackForm.category" style="width: 100%">
            <el-option label="问题" value="question" />
            <el-option label="建议" value="suggestion" />
            <el-option label="表扬" value="praise" />
            <el-option label="缺陷" value="bug" />
          </el-select>
        </el-form-item>
        <el-form-item label="反馈人">
          <el-input v-model="feedbackForm.raised_by" placeholder="可选" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="feedbackForm.content" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddFeedbackDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingFeedback" @click="handleAddFeedback">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Calendar, Location, Link, Plus } from '@element-plus/icons-vue'
import {
  getEvent,
  createEvent,
  getChecklist,
  updateChecklistItem,
  listPersonnel,
  addPersonnel,
  confirmPersonnel,
  listFeedback,
  createFeedback,
  updateFeedback,
  listTasks,
  createTask,
  deleteTask,
  updateEventStatus,
  updateEvent,
} from '../api/event'
import type { EventDetail, ChecklistItem, Personnel, FeedbackItem, EventTask } from '../api/event'

const route = useRoute()
const router = useRouter()
// 两种进入方式：静态路由 /events/new (name=EventNew, 无 :id 参数) 或动态路由 /events/:id
const isNewEvent = computed(() => route.name === 'EventNew' || route.params.id === 'new')
const eventId = computed(() => isNewEvent.value ? undefined : Number(route.params.id))

// ─── State ────────────────────────────────────────────────────────────────────
const loading = ref(false)
const event = ref<EventDetail | null>(null)
const activeTab = ref('checklist')

const checklistLoading = ref(false)
const checklist = ref<ChecklistItem[]>([])

const personnelLoading = ref(false)
const personnel = ref<Personnel[]>([])

const tasksLoading = ref(false)
const tasks = ref<EventTask[]>([])

const feedbackLoading = ref(false)
const feedback = ref<FeedbackItem[]>([])

// Dialog states
const showAddTaskDialog = ref(false)
const showAddPersonnelDialog = ref(false)
const showAddFeedbackDialog = ref(false)
const savingTask = ref(false)
const savingPersonnel = ref(false)
const savingFeedback = ref(false)

const isEditing = ref(false)
const saving = ref(false)
const editForm = ref({
  title: '',
  planned_at: null as string | null,
  duration_minutes: null as number | null,
  location: '',
  online_url: '',
  description: '',
  status: 'draft' as string,
})

const ganttEl = ref<HTMLElement | null>(null)

const taskForm = ref({ title: '', task_type: 'task', phase: 'pre', start_date: null as string | null, end_date: null as string | null })
const personnelForm = ref({ role: '', role_label: '', assignee_type: 'internal', time_slot: '', notes: '' })
const feedbackForm = ref({ category: 'question', raised_by: '', content: '' })

// ─── Labels & Maps ────────────────────────────────────────────────────────────
const statusLabel: Record<string, string> = { draft: '草稿', planning: '策划中', ongoing: '进行中', completed: '已完成', cancelled: '已取消' }
const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { draft: 'info', planning: 'warning', ongoing: 'primary', completed: 'success', cancelled: 'danger' }
const typeLabel: Record<string, string> = { offline: '线下', online: '线上', hybrid: '混合' }
const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { offline: '', online: 'success', hybrid: 'warning' }
const phaseLabel: Record<string, string> = { pre: '会前', during: '会中', post: '会后' }
const taskStatusLabel: Record<string, string> = { not_started: '未开始', in_progress: '进行中', done: '已完成', blocked: '阻塞中' }
const taskStatusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { not_started: 'info', in_progress: 'primary', done: 'success', blocked: 'danger' }
const confirmLabel: Record<string, string> = { pending: '待确认', confirmed: '已确认', declined: '已拒绝' }
const confirmTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { pending: 'warning', confirmed: 'success', declined: 'danger' }
const feedbackCategoryLabel: Record<string, string> = { question: '问题', suggestion: '建议', praise: '表扬', bug: '缺陷' }
const feedbackTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { question: 'info', suggestion: 'primary', praise: 'success', bug: 'danger' }
const feedbackStatusLabel: Record<string, string> = { open: '待处理', in_progress: '处理中', closed: '已关闭' }

const phases = [
  { key: 'pre' as const, label: '会前准备' },
  { key: 'during' as const, label: '会中执行' },
  { key: 'post' as const, label: '会后复盘' },
]

// ─── Computed ─────────────────────────────────────────────────────────────────
const checklistByPhase = computed(() => ({
  pre: checklist.value.filter(i => i.phase === 'pre'),
  during: checklist.value.filter(i => i.phase === 'during'),
  post: checklist.value.filter(i => i.phase === 'post'),
}))

/** 将树形任务拍平，用于 table 显示 */
function flattenTasks(nodes: EventTask[]): EventTask[] {
  const result: EventTask[] = []
  for (const node of nodes) {
    result.push(node)
    if (node.children?.length) result.push(...flattenTasks(node.children))
  }
  return result
}

const flatTasks = computed(() => flattenTasks(tasks.value))

/** 过滤出有完整起止日期的任务，供甘特图使用 */
const ganttTasks = computed(() =>
  flatTasks.value.filter(t => t.start_date && t.end_date)
)

// ─── Utils ────────────────────────────────────────────────────────────────────
function formatDateTime(dt: string | null): string {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatDate(dt: string): string {
  return new Date(dt).toLocaleDateString('zh-CN')
}

// ─── Load Data ────────────────────────────────────────────────────────────────
async function loadEvent() {
  loading.value = true
  try {
    if (isNewEvent.value) {
      event.value = null
      isEditing.value = true
      editForm.value = {
        title: '',
        planned_at: null,
        duration_minutes: null,
        location: '',
        online_url: '',
        description: '',
        status: 'draft',
      }
    } else {
      event.value = await getEvent(eventId.value!)
    }
  } catch {
    ElMessage.error('加载活动详情失败')
  } finally {
    loading.value = false
  }
}

async function loadChecklist() {
  if (isNewEvent.value || !eventId.value) return
  checklistLoading.value = true
  try { checklist.value = await getChecklist(eventId.value!) } catch {} finally { checklistLoading.value = false }
}

async function loadPersonnel() {
  if (isNewEvent.value || !eventId.value) return
  personnelLoading.value = true
  try { personnel.value = await listPersonnel(eventId.value!) } catch {} finally { personnelLoading.value = false }
}

async function loadTasks() {
  if (isNewEvent.value || !eventId.value) return
  tasksLoading.value = true
  try { tasks.value = await listTasks(eventId.value!) } catch {} finally { tasksLoading.value = false }
}

async function loadFeedback() {
  if (isNewEvent.value || !eventId.value) return
  feedbackLoading.value = true
  try { feedback.value = await listFeedback(eventId.value!) } catch {} finally { feedbackLoading.value = false }
}

// ─── Actions ──────────────────────────────────────────────────────────────────
function startEdit() {
  if (!event.value) return
  editForm.value = {
    title: event.value.title,
    planned_at: event.value.planned_at,
    duration_minutes: event.value.duration_minutes,
    location: event.value.location || '',
    online_url: event.value.online_url || '',
    description: event.value.description || '',
    status: event.value.status,
  }
  isEditing.value = true
}

function cancelEdit() {
  if (isNewEvent.value) {
    router.push('/events')
  } else {
    isEditing.value = false
  }
}

async function saveEdit() {
  if (!editForm.value.title.trim()) {
    ElMessage.warning('请输入活动名称')
    return
  }
  saving.value = true
  try {
    if (isNewEvent.value) {
      const newEvent = await createEvent({
        title: editForm.value.title,
        planned_at: editForm.value.planned_at || null,
        duration_minutes: editForm.value.duration_minutes || null,
        location: editForm.value.location || null,
        online_url: editForm.value.online_url || null,
        description: editForm.value.description || null,
        status: editForm.value.status,
      })
      router.push(`/events/${newEvent.id}`)
    } else {
      await updateEvent(eventId.value!, {
        title: editForm.value.title,
        planned_at: editForm.value.planned_at,
        duration_minutes: editForm.value.duration_minutes,
        location: editForm.value.location || null,
        online_url: editForm.value.online_url || null,
        description: editForm.value.description || null,
      })
      await loadEvent()
      isEditing.value = false
    }
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  if (!eventId.value) return
  try {
    await updateEventStatus(eventId.value!, newStatus)
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('状态更新失败')
  }
}

async function toggleChecklist(item: ChecklistItem, checked: boolean) {
  if (!eventId.value) return
  const newStatus = checked ? 'done' : 'pending'
  try {
    const updated = await updateChecklistItem(eventId.value, item.id, { status: newStatus })
    const idx = checklist.value.findIndex(i => i.id === item.id)
    if (idx !== -1) checklist.value[idx] = updated
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleAddTask() {
  if (!eventId.value) return
  if (!taskForm.value.title.trim()) { ElMessage.warning('请输入任务名称'); return }
  savingTask.value = true
  try {
    await createTask(eventId.value!, {
      title: taskForm.value.title,
      task_type: taskForm.value.task_type,
      phase: taskForm.value.phase,
      start_date: taskForm.value.start_date || null,
      end_date: taskForm.value.end_date || null,
    })
    showAddTaskDialog.value = false
    await loadTasks()
  } catch {
    ElMessage.error('添加任务失败')
  } finally {
    savingTask.value = false }
}

async function handleDeleteTask(tid: number) {
  if (!eventId.value) return
  try {
    await ElMessageBox.confirm('确定删除此任务？', '确认', { type: 'warning' })
    await deleteTask(eventId.value!, tid)
    await loadTasks()
  } catch { /* cancelled */ }
}

async function handleConfirmPersonnel(pid: number, confirmed: string) {
  if (!eventId.value) return
  try {
    await confirmPersonnel(eventId.value!, pid, confirmed)
    await loadPersonnel()
    ElMessage.success(confirmed === 'confirmed' ? '已确认' : '已拒绝')
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleAddPersonnel() {
  if (!eventId.value) return
  if (!personnelForm.value.role.trim()) { ElMessage.warning('请填写角色'); return }
  savingPersonnel.value = true
  try {
    await addPersonnel(eventId.value, {
      role: personnelForm.value.role,
      role_label: personnelForm.value.role_label || null,
      assignee_type: personnelForm.value.assignee_type,
      time_slot: personnelForm.value.time_slot || null,
      notes: personnelForm.value.notes || null,
    })
    showAddPersonnelDialog.value = false
    await loadPersonnel()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    savingPersonnel.value = false
  }
}

async function handleAddFeedback() {
  if (!eventId.value) return
  if (!feedbackForm.value.content.trim()) { ElMessage.warning('请填写反馈内容'); return }
  savingFeedback.value = true
  try {
    await createFeedback(eventId.value, {
      content: feedbackForm.value.content,
      category: feedbackForm.value.category,
      raised_by: feedbackForm.value.raised_by || undefined,
    })
    showAddFeedbackDialog.value = false
    await loadFeedback()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingFeedback.value = false
  }
}

async function handleUpdateFeedbackStatus(fid: number, status: string) {
  if (!eventId.value) return
  try {
    await updateFeedback(eventId.value, fid, { status })
    const idx = feedback.value.findIndex(f => f.id === fid)
    if (idx !== -1) feedback.value[idx].status = status
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('更新失败')
  }
}

// ─── Gantt Chart ──────────────────────────────────────────────────────────────
async function renderGantt() {
  if (!ganttEl.value || ganttTasks.value.length === 0) return
  try {
    const { default: Gantt } = await import('frappe-gantt')
    ganttEl.value.innerHTML = ''
    new Gantt(ganttEl.value, ganttTasks.value.map(t => ({
      id: String(t.id),
      name: t.title,
      start: t.start_date!,
      end: t.end_date!,
      progress: t.progress,
      dependencies: t.depends_on.join(','),
    })), { view_mode: 'Week', language: 'zh' })
  } catch {
    // frappe-gantt not available; table view is sufficient
  }
}

// Re-render gantt when tasks change and tab is visible
watch([ganttTasks, activeTab], async ([, tab]) => {
  if (tab === 'tasks') {
    await nextTick()
    renderGantt()
  }
})

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadEvent()
  // Load all tabs data in parallel
  await Promise.all([loadChecklist(), loadPersonnel(), loadTasks(), loadFeedback()])
})
</script>

<style scoped>
.event-detail {
  padding: 24px 32px;
  max-width: 1100px;
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
  margin-bottom: 12px;
  gap: 16px;
}

.info-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
}

.event-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.info-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.info-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.info-meta-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #475569;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.meta-sub {
  color: #94a3b8;
}

.edit-form {
  margin-bottom: 12px;
}

.event-description {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
}

.detail-tabs {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0 16px 16px;
}

.tab-content {
  padding: 16px 0;
  min-height: 200px;
}

.tab-actions {
  margin-bottom: 16px;
}

.tab-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: #94a3b8;
  font-size: 14px;
}

/* Checklist */
.checklist-phase {
  margin-bottom: 20px;
}

.phase-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.phase-empty {
  font-size: 13px;
  color: #cbd5e1;
  padding: 4px 0;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
}

.checklist-item.done .checklist-title {
  text-decoration: line-through;
  color: #94a3b8;
}

.checklist-title {
  flex: 1;
  font-size: 14px;
  color: #1e293b;
}

/* Feedback */
.feedback-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
}

.feedback-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.feedback-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-left: auto;
}

.feedback-actions {
  display: flex;
  gap: 8px;
}

.feedback-content {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
}

.issue-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.issue-link {
  font-size: 12px;
  color: #0095ff;
  text-decoration: none;
}

.issue-link:hover {
  text-decoration: underline;
}

/* Gantt */
.gantt-wrapper {
  margin-top: 8px;
}

.gantt-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.gantt-container {
  overflow-x: auto;
}

/* frappe-gantt global override (scoped doesn't apply to library DOM) */
:deep(.gantt-container) svg {
  font-family: inherit;
}
</style>
