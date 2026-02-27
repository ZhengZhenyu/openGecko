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
            <h1 class="event-title">{{ isNewEvent ? '创建活动' : (isEditing ? editForm.title : event?.title) }}</h1>
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
            <el-button
              v-if="!isNewEvent && event"
              size="small"
              type="danger"
              link
              @click="handleDeleteEvent"
            >删除活动</el-button>
          </div>
        </div>

        <div v-if="!isEditing && event" class="info-meta-grid">
          <div v-if="event.planned_at" class="meta-item">
            <el-icon><Calendar /></el-icon>
            <span>{{ formatDateTime(event.planned_at) }}</span>
            <span v-if="event.duration_hours" class="meta-sub">（{{ event.duration_hours }} 小时）</span>
          </div>
          <div v-if="event.location" class="meta-item">
            <el-icon><Location /></el-icon>
            <span>{{ event.location }}</span>
          </div>
          <div v-if="event.online_url" class="meta-item">
            <el-icon><Link /></el-icon>
            <a :href="event.online_url" target="_blank">{{ event.online_url }}</a>
          </div>
          <div v-if="event.communities && event.communities.length > 0" class="meta-item">
            <el-icon><Connection /></el-icon>
            <el-tag
              v-for="c in event.communities"
              :key="c.id"
              size="small"
              style="margin-right:4px"
            >{{ c.name }}</el-tag>
          </div>
        </div>

        <div v-else class="edit-form">
          <el-form :model="editForm" label-width="90px" size="small">
            <el-form-item v-if="isNewEvent" label="SOP 模板">
              <el-select
                v-model="editForm.template_id"
                clearable
                placeholder="选择模板（可选）"
                style="width:100%"
                @change="onTemplateChange"
              >
                <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
              </el-select>
              <div v-if="selectedTemplate" style="margin-top:4px;color:#64748b;font-size:12px">
                将自动生成 {{ selectedTemplate.checklist_items.length }} 条清单项
              </div>
            </el-form-item>
            <el-form-item label="活动名称">
              <el-input v-model="editForm.title" />
            </el-form-item>
            <el-form-item label="活动类型">
              <el-select v-model="editForm.event_type" style="width: 100%">
                <el-option label="线下" value="offline" />
                <el-option label="线上" value="online" />
                <el-option label="混合" value="hybrid" />
              </el-select>
            </el-form-item>
            <el-form-item label="活动状态">
              <el-select v-model="editForm.status" style="width: 100%">
                <el-option label="策划中" value="planning" />
                <el-option label="进行中" value="ongoing" />
                <el-option label="已完成" value="completed" />
              </el-select>
            </el-form-item>
            <el-form-item label="计划时间">
              <el-date-picker v-model="editForm.planned_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
            </el-form-item>
            <el-form-item label="时长（小时）">
              <el-input-number v-model="editForm.duration_hours" :min="0" :step="0.5" :precision="1" style="width: 100%" />
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
            <el-form-item label="关联社区">
              <el-select
                v-model="editForm.community_ids"
                multiple
                style="width: 100%"
                placeholder="选择关联社区（可多选）"
              >
                <el-option
                  v-for="c in authStore.communities"
                  :key="c.id"
                  :label="c.name"
                  :value="c.id"
                />
              </el-select>
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
            <div class="tab-actions">
              <el-button size="small" type="primary" @click="handleAddChecklistItem('pre')">
                <el-icon><Plus /></el-icon>添加清单项
              </el-button>
              <el-button size="small" @click="openImportTemplateDialog">
                从模板导入
              </el-button>
            </div>
            <div v-if="checklistByPhase.pre.length || checklistByPhase.during.length || checklistByPhase.post.length">
              <div v-for="phase in phases" :key="phase.key" class="checklist-phase">
                <div class="phase-header">
                  <h4 class="phase-title">{{ phase.label }}</h4>
                  <el-button link size="small" class="phase-add-btn" @click="handleAddChecklistItem(phase.key)">
                    <el-icon><Plus /></el-icon>添加
                  </el-button>
                </div>
                <div v-if="checklistByPhase[phase.key].length === 0" class="phase-empty">本阶段无清单项</div>
                <div
                  v-for="item in checklistByPhase[phase.key]"
                  :key="item.id"
                  class="checklist-item"
                  :class="{ done: item.status === 'done' }"
                >
                  <div class="checklist-row">
                    <el-checkbox
                      :model-value="item.status === 'done'"
                      @change="(v: boolean) => toggleChecklist(item, v)"
                    />
                    <span class="checklist-title">{{ item.title }}</span>
                    <span v-if="item.responsible_role" class="role-badge">{{ item.responsible_role }}</span>
                    <span v-if="item.assignee_ids && item.assignee_ids.length" class="checklist-assignees">
                      <el-tag
                        v-for="uid in item.assignee_ids"
                        :key="uid"
                        size="small"
                        type="info"
                        style="margin-left:4px;flex-shrink:0"
                      >{{ getUserName(uid) }}</el-tag>
                    </span>
                    <el-tag v-if="item.is_mandatory" type="danger" size="small" style="margin-left:4px;flex-shrink:0">必须</el-tag>
                    <el-tag v-if="item.status === 'done'" type="success" size="small" style="margin-left:4px;flex-shrink:0">已完成</el-tag>
                    <el-icon
                      v-if="item.description"
                      class="expand-btn"
                      :class="{ expanded: expandedItems.has(item.id) }"
                      @click="toggleExpand(item.id)"
                    ><ArrowRight /></el-icon>
                    <div class="item-actions">
                      <el-button link size="small" @click="handleEditChecklistItem(item)">编辑</el-button>
                      <el-button link size="small" type="danger" @click="handleDeleteChecklistItem(item)">删除</el-button>
                    </div>
                  </div>
                  <div v-if="item.description && expandedItems.has(item.id)" class="item-description">
                    {{ item.description }}
                    <a v-if="item.reference_url" :href="item.reference_url" target="_blank" class="ref-link">参考链接 →</a>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="tab-empty">暂无清单项，点击「添加清单项」或创建活动时选择模板可自动生成</div>
          </div>
        </el-tab-pane>

        <!-- 任务规划 Tab (甘特图) -->
        <el-tab-pane label="任务规划" name="tasks">
          <div v-loading="tasksLoading" class="tab-content">
            <div class="tab-actions">
              <el-button size="small" type="primary" @click="handleOpenAddTask">
                <el-icon><Plus /></el-icon>添加任务
              </el-button>
            </div>

            <!-- Task list table -->
            <el-table :data="flatTasks" row-key="id" style="width: 100%; margin-bottom: 24px">
              <el-table-column label="任务名称" prop="title" min-width="160">
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
              <el-table-column label="责任人" min-width="130">
                <template #default="{ row }">
                  <span v-if="row.assignee_ids && row.assignee_ids.length">
                    <el-tag
                      v-for="uid in row.assignee_ids"
                      :key="uid"
                      size="small"
                      style="margin-right:4px;margin-bottom:2px"
                    >{{ getUserName(uid) }}</el-tag>
                  </span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
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
              <el-table-column label="操作" width="110">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="handleEditTask(row)">编辑</el-button>
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

    <!-- Add/Edit Task Dialog -->
    <el-dialog v-model="showTaskDialog" :title="editingTask ? '编辑任务' : '添加任务'" width="500px" destroy-on-close>
      <el-form :model="taskForm" label-width="90px">
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
        <el-form-item label="进度 (%)">
          <el-input-number v-model="taskForm.progress" :min="0" :max="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="taskForm.status" style="width: 100%">
            <el-option label="未开始" value="not_started" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="阻塞中" value="blocked" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任人">
          <el-select
            v-model="taskForm.assignee_ids"
            multiple
            style="width: 100%"
            placeholder="选择责任人（可多选）"
          >
            <el-option
              v-for="u in communityUsers"
              :key="u.id"
              :label="(u.full_name || u.username) + (u.full_name ? ` (@${u.username})` : '')"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTaskDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingTask" @click="handleSaveTask">{{ editingTask ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- Import from Template Dialog -->
    <el-dialog v-model="showImportTemplateDialog" title="从模板导入清单" width="540px" destroy-on-close>
      <div class="import-template-body">
        <div class="import-template-selector">
          <span class="import-label">选择模板</span>
          <el-select
            v-model="importTemplateId"
            placeholder="请选择 SOP 模板"
            style="flex:1"
            @change="onImportTemplateChange"
          >
            <el-option v-for="t in templateList" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </div>

        <div v-if="importingTemplateDetail" v-loading="loadingImportTemplate" class="import-preview">
          <div v-for="phase in phases" :key="phase.key" class="import-phase">
            <template v-if="importItemsByPhase[phase.key].length > 0">
              <div class="import-phase-title">{{ phase.label }}</div>
              <div
                v-for="item in importItemsByPhase[phase.key]"
                :key="item.id"
                class="import-item-row"
              >
                <el-tag v-if="item.is_mandatory" type="danger" size="small" class="import-mandatory">必须</el-tag>
                <span class="import-item-title">{{ item.title }}</span>
                <span v-if="item.responsible_role" class="import-item-role">{{ item.responsible_role }}</span>
              </div>
            </template>
          </div>
          <div v-if="importTotalCount === 0" class="import-empty">该模板暂无清单条目</div>
          <div v-else class="import-count">共 {{ importTotalCount }} 条清单项将被导入</div>
        </div>
        <div v-else-if="!importTemplateId" class="import-empty">请先选择一个模板</div>
      </div>
      <template #footer>
        <el-button @click="showImportTemplateDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="importingChecklist"
          :disabled="!importTemplateId || importTotalCount === 0"
          @click="handleImportFromTemplate"
        >
          导入 {{ importTotalCount > 0 ? `(${importTotalCount} 条)` : '' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Add/Edit Checklist Item Dialog -->
    <el-dialog
      v-model="showChecklistItemDialog"
      :title="editingChecklistItem ? '编辑清单项' : '添加清单项'"
      width="480px"
      destroy-on-close
    >
      <el-form :model="checklistItemForm" label-width="90px">
        <el-form-item label="阶段" required>
          <el-select v-model="checklistItemForm.phase" style="width: 100%">
            <el-option label="会前准备" value="pre" />
            <el-option label="会中执行" value="during" />
            <el-option label="会后复盘" value="post" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="checklistItemForm.title" placeholder="清单项标题" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="checklistItemForm.description" type="textarea" :rows="3" placeholder="可选，操作说明或指引" />
        </el-form-item>
        <el-form-item label="负责角色">
          <el-input v-model="checklistItemForm.responsible_role" placeholder="如：主持人、后勤组" />
        </el-form-item>
        <el-form-item label="参考链接">
          <el-input v-model="checklistItemForm.reference_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="checklistItemForm.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="checklistItemForm.notes" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="责任人">
          <el-select
            v-model="checklistItemForm.assignee_ids"
            multiple
            style="width: 100%"
            placeholder="选择责任人（可多选）"
          >
            <el-option
              v-for="u in communityUsers"
              :key="u.id"
              :label="(u.full_name || u.username) + (u.full_name ? ` (@${u.username})` : '')"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="必须完成">
          <el-switch v-model="checklistItemForm.is_mandatory" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChecklistItemDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingChecklistItem" @click="handleSaveChecklistItem">
          {{ editingChecklistItem ? '保存' : '添加' }}
        </el-button>
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
import { ArrowLeft, Calendar, Location, Link, Plus, Connection, ArrowRight } from '@element-plus/icons-vue'
import { useCommunityStore } from '../stores/community'
import { useAuthStore } from '../stores/auth'
import { getCommunityUsers } from '../api/community'
import type { CommunityUser } from '../api/community'
import {
  getEvent,
  createEvent,
  getChecklist,
  updateChecklistItem,
  createChecklistItem,
  deleteChecklistItem,
  listFeedback,
  createFeedback,
  updateFeedback,
  listTasks,
  createTask,
  updateTask,
  deleteTask,
  deleteEvent,
  updateEventStatus,
  updateEvent,
  listTemplates,
  getTemplate,
} from '../api/event'
import type { EventDetail, ChecklistItem, FeedbackItem, EventTask, EventTemplateListItem, EventTemplate } from '../api/event'

const route = useRoute()
const router = useRouter()
const communityStore = useCommunityStore()
const authStore = useAuthStore()
// 两种进入方式：静态路由 /events/new (name=EventNew, 无 :id 参数) 或动态路由 /events/:id
const isNewEvent = computed(() => route.name === 'EventNew' || route.params.id === 'new')
const eventId = computed(() => isNewEvent.value ? undefined : Number(route.params.id))

// ─── State ────────────────────────────────────────────────────────────────────
const loading = ref(false)
const event = ref<EventDetail | null>(null)
const activeTab = ref('checklist')

const checklistLoading = ref(false)
const checklist = ref<ChecklistItem[]>([])

const tasksLoading = ref(false)
const tasks = ref<EventTask[]>([])

const feedbackLoading = ref(false)
const feedback = ref<FeedbackItem[]>([])

// Community users for assignee selector
const communityUsers = ref<CommunityUser[]>([])

// Dialog states
const showTaskDialog = ref(false)
const editingTask = ref<EventTask | null>(null)
const showAddFeedbackDialog = ref(false)
const savingTask = ref(false)
const savingFeedback = ref(false)

// Checklist item dialog
const showChecklistItemDialog = ref(false)
const editingChecklistItem = ref<ChecklistItem | null>(null)
const checklistItemForm = ref({
  phase: 'pre' as string,
  title: '',
  description: '',
  is_mandatory: false,
  responsible_role: '',
  reference_url: '',
  due_date: null as string | null,
  notes: '',
  assignee_ids: [] as number[],
})
const savingChecklistItem = ref(false)

// Import template dialog
const showImportTemplateDialog = ref(false)
const importTemplateId = ref<number | null>(null)
const importingTemplateDetail = ref<EventTemplate | null>(null)
const loadingImportTemplate = ref(false)
const importingChecklist = ref(false)

const importItemsByPhase = computed(() => ({
  pre: importingTemplateDetail.value?.checklist_items.filter(i => i.phase === 'pre') ?? [],
  during: importingTemplateDetail.value?.checklist_items.filter(i => i.phase === 'during') ?? [],
  post: importingTemplateDetail.value?.checklist_items.filter(i => i.phase === 'post') ?? [],
}))

const importTotalCount = computed(() =>
  (importingTemplateDetail.value?.checklist_items.length ?? 0)
)

const isEditing = ref(false)
const saving = ref(false)
const editForm = ref({
  title: '',
  event_type: 'offline' as string,
  planned_at: null as string | null,
  duration_hours: null as number | null,
  location: '',
  online_url: '',
  description: '',
  status: 'planning' as string,
  community_ids: [] as number[],
  template_id: null as number | null,
})

// ─── Template ─────────────────────────────────────────────────────────────────
const templateList = ref<EventTemplateListItem[]>([])
const selectedTemplate = ref<EventTemplate | null>(null)
const expandedItems = ref(new Set<number>())

function toggleExpand(id: number) {
  if (expandedItems.value.has(id)) {
    expandedItems.value.delete(id)
  } else {
    expandedItems.value.add(id)
  }
}

async function onTemplateChange(val: number | null) {
  if (val) {
    try {
      selectedTemplate.value = await getTemplate(val)
    } catch {
      selectedTemplate.value = null
    }
  } else {
    selectedTemplate.value = null
  }
}

const ganttEl = ref<HTMLElement | null>(null)

const taskForm = ref({
  title: '',
  task_type: 'task' as string,
  phase: 'pre' as string,
  start_date: null as string | null,
  end_date: null as string | null,
  progress: 0,
  status: 'not_started' as string,
  assignee_ids: [] as number[],
})
const feedbackForm = ref({ category: 'question', raised_by: '', content: '' })

// ─── Labels & Maps ────────────────────────────────────────────────────────────
const statusLabel: Record<string, string> = { planning: '策划中', ongoing: '进行中', completed: '已完成' }
const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { planning: 'warning', ongoing: 'primary', completed: 'success' }
const typeLabel: Record<string, string> = { offline: '线下', online: '线上', hybrid: '混合' }
const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { offline: '', online: 'success', hybrid: 'warning' }
const phaseLabel: Record<string, string> = { pre: '会前', during: '会中', post: '会后' }
const taskStatusLabel: Record<string, string> = { not_started: '未开始', in_progress: '进行中', completed: '已完成', blocked: '阻塞中' }
const taskStatusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { not_started: 'info', in_progress: 'primary', completed: 'success', blocked: 'danger' }
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
        event_type: 'offline',
        planned_at: null,
        duration_hours: null,
        location: '',
        online_url: '',
        description: '',
        status: 'planning',
        community_ids: communityStore.currentCommunityId ? [communityStore.currentCommunityId] : [],
        template_id: null,
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

async function loadCommunityUsers() {
  const cid = communityStore.currentCommunityId
  if (!cid) return
  try {
    communityUsers.value = await getCommunityUsers(cid)
  } catch {
    communityUsers.value = []
  }
}

function getUserName(userId: number): string {
  const u = communityUsers.value.find(u => u.id === userId)
  return u ? (u.full_name || u.username) : String(userId)
}

// ─── Actions ──────────────────────────────────────────────────────────────────
function startEdit() {
  if (!event.value) return
  editForm.value = {
    title: event.value.title,
    event_type: event.value.event_type,
    planned_at: event.value.planned_at,
    duration_hours: event.value.duration_hours,
    location: event.value.location || '',
    online_url: event.value.online_url || '',
    description: event.value.description || '',
    status: event.value.status,
    community_ids: event.value.community_ids?.length
      ? [...event.value.community_ids]
      : (event.value.community_id ? [event.value.community_id] : []),
    template_id: event.value.template_id,
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
      const communityIds = editForm.value.community_ids
      const newEvent = await createEvent({
        title: editForm.value.title,
        event_type: editForm.value.event_type,
        planned_at: editForm.value.planned_at || null,
        duration_hours: editForm.value.duration_hours || null,
        location: editForm.value.location || null,
        online_url: editForm.value.online_url || null,
        description: editForm.value.description || null,
        status: editForm.value.status,
        community_id: communityIds[0] || null,
        community_ids: communityIds,
        template_id: editForm.value.template_id || null,
      })
      router.push(`/events/${newEvent.id}`)
    } else {
      await updateEvent(eventId.value!, {
        title: editForm.value.title,
        event_type: editForm.value.event_type,
        planned_at: editForm.value.planned_at,
        duration_hours: editForm.value.duration_hours,
        location: editForm.value.location || null,
        online_url: editForm.value.online_url || null,
        description: editForm.value.description || null,
        community_ids: editForm.value.community_ids,
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

function handleOpenAddTask() {
  editingTask.value = null
  taskForm.value = {
    title: '',
    task_type: 'task',
    phase: 'pre',
    start_date: null,
    end_date: null,
    progress: 0,
    status: 'not_started',
    assignee_ids: [],
  }
  showTaskDialog.value = true
}

function handleEditTask(task: EventTask) {
  editingTask.value = task
  taskForm.value = {
    title: task.title,
    task_type: task.task_type,
    phase: task.phase,
    start_date: task.start_date,
    end_date: task.end_date,
    progress: task.progress,
    status: task.status,
    assignee_ids: [...(task.assignee_ids || [])],
  }
  showTaskDialog.value = true
}

async function handleSaveTask() {
  if (!eventId.value) return
  if (!taskForm.value.title.trim()) { ElMessage.warning('请输入任务名称'); return }
  savingTask.value = true
  try {
    const payload = {
      title: taskForm.value.title,
      task_type: taskForm.value.task_type,
      phase: taskForm.value.phase,
      start_date: taskForm.value.start_date || null,
      end_date: taskForm.value.end_date || null,
      progress: taskForm.value.progress,
      status: taskForm.value.status,
      assignee_ids: taskForm.value.assignee_ids,
    }
    if (editingTask.value) {
      await updateTask(eventId.value!, editingTask.value.id, payload)
      ElMessage.success('任务已更新')
    } else {
      await createTask(eventId.value!, payload)
      ElMessage.success('任务已添加')
    }
    showTaskDialog.value = false
    await loadTasks()
  } catch {
    ElMessage.error(editingTask.value ? '更新任务失败' : '添加任务失败')
  } finally {
    savingTask.value = false
  }
}

async function handleDeleteTask(tid: number) {
  if (!eventId.value) return
  try {
    await ElMessageBox.confirm('确定删除此任务？', '确认', { type: 'warning' })
    await deleteTask(eventId.value!, tid)
    await loadTasks()
  } catch { /* cancelled */ }
}

async function handleDeleteEvent() {
  if (!eventId.value || !event.value) return
  try {
    await ElMessageBox.confirm(
      `确定要永久删除活动「${event.value.title}」吗？此操作不可撤销。`,
      '删除活动',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteEvent(eventId.value)
    ElMessage.success('活动已删除')
    router.push('/events')
  } catch {
    ElMessage.error('删除失败，请重试')
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

// ─── Checklist Item CRUD ──────────────────────────────────────────────────────
function handleAddChecklistItem(phase: string) {
  editingChecklistItem.value = null
  checklistItemForm.value = {
    phase,
    title: '',
    description: '',
    is_mandatory: false,
    responsible_role: '',
    reference_url: '',
    due_date: null,
    notes: '',
    assignee_ids: [],
  }
  showChecklistItemDialog.value = true
}

function handleEditChecklistItem(item: ChecklistItem) {
  editingChecklistItem.value = item
  checklistItemForm.value = {
    phase: item.phase,
    title: item.title,
    description: item.description || '',
    is_mandatory: item.is_mandatory,
    responsible_role: item.responsible_role || '',
    reference_url: item.reference_url || '',
    due_date: item.due_date || null,
    notes: item.notes || '',
    assignee_ids: [...(item.assignee_ids || [])],
  }
  showChecklistItemDialog.value = true
}

async function handleDeleteChecklistItem(item: ChecklistItem) {
  if (!eventId.value) return
  try {
    await ElMessageBox.confirm(`确定删除清单项「${item.title}」？`, '确认', { type: 'warning' })
    await deleteChecklistItem(eventId.value, item.id)
    checklist.value = checklist.value.filter(i => i.id !== item.id)
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

async function handleSaveChecklistItem() {
  if (!eventId.value) return
  if (!checklistItemForm.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  savingChecklistItem.value = true
  try {
    if (editingChecklistItem.value) {
      const updated = await updateChecklistItem(eventId.value, editingChecklistItem.value.id, {
        phase: checklistItemForm.value.phase,
        title: checklistItemForm.value.title,
        description: checklistItemForm.value.description || null,
        is_mandatory: checklistItemForm.value.is_mandatory,
        responsible_role: checklistItemForm.value.responsible_role || null,
        reference_url: checklistItemForm.value.reference_url || null,
        due_date: checklistItemForm.value.due_date || null,
        notes: checklistItemForm.value.notes || null,
        assignee_ids: checklistItemForm.value.assignee_ids,
      })
      const idx = checklist.value.findIndex(i => i.id === editingChecklistItem.value!.id)
      if (idx !== -1) checklist.value[idx] = updated
      ElMessage.success('已更新')
    } else {
      const created = await createChecklistItem(eventId.value, {
        phase: checklistItemForm.value.phase,
        title: checklistItemForm.value.title,
        description: checklistItemForm.value.description || null,
        is_mandatory: checklistItemForm.value.is_mandatory,
        responsible_role: checklistItemForm.value.responsible_role || null,
        reference_url: checklistItemForm.value.reference_url || null,
        due_date: checklistItemForm.value.due_date || null,
        notes: checklistItemForm.value.notes || null,
        assignee_ids: checklistItemForm.value.assignee_ids,
      })
      checklist.value.push(created)
      ElMessage.success('已添加')
    }
    showChecklistItemDialog.value = false
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingChecklistItem.value = false
  }
}

// ─── Import Template ──────────────────────────────────────────────────────────
function openImportTemplateDialog() {
  importTemplateId.value = null
  importingTemplateDetail.value = null
  showImportTemplateDialog.value = true
}

async function onImportTemplateChange(id: number | null) {
  if (!id) { importingTemplateDetail.value = null; return }
  loadingImportTemplate.value = true
  try {
    importingTemplateDetail.value = await getTemplate(id)
  } catch {
    ElMessage.error('加载模板详情失败')
    importingTemplateDetail.value = null
  } finally {
    loadingImportTemplate.value = false
  }
}

async function handleImportFromTemplate() {
  if (!eventId.value || !importingTemplateDetail.value) return
  importingChecklist.value = true
  try {
    const items = importingTemplateDetail.value.checklist_items
    const plannedAt = event.value?.planned_at ? new Date(event.value.planned_at) : null

    const created = await Promise.all(items.map(item => {
      let dueDate: string | null = null
      if (item.deadline_offset_days !== null && plannedAt) {
        const d = new Date(plannedAt)
        d.setDate(d.getDate() + item.deadline_offset_days)
        dueDate = d.toISOString().split('T')[0]
      }
      return createChecklistItem(eventId.value!, {
        phase: item.phase,
        title: item.title,
        description: item.description ?? null,
        is_mandatory: item.is_mandatory,
        responsible_role: item.responsible_role ?? null,
        reference_url: item.reference_url ?? null,
        due_date: dueDate,
        order: item.order,
      })
    }))

    checklist.value.push(...created)
    ElMessage.success(`已导入 ${created.length} 条清单项`)
    showImportTemplateDialog.value = false
  } catch {
    ElMessage.error('导入失败，请重试')
  } finally {
    importingChecklist.value = false
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
  // Load template list for new event form
  try {
    templateList.value = await listTemplates()
  } catch {
    templateList.value = []
  }
  await loadEvent()
  await loadCommunityUsers()
  // Load all tabs data in parallel
  await Promise.all([loadChecklist(), loadTasks(), loadFeedback()])
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

.phase-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.phase-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.phase-add-btn {
  font-size: 12px;
  color: #94a3b8;
  opacity: 0;
  transition: opacity 0.15s;
}

.checklist-phase:hover .phase-add-btn {
  opacity: 1;
}

.phase-empty {
  font-size: 13px;
  color: #cbd5e1;
  padding: 4px 0;
}

.checklist-item {
  display: flex;
  flex-direction: column;
  padding: 6px 0;
  border-bottom: 1px solid #f1f5f9;
}

.checklist-row {
  display: flex;
  align-items: center;
  gap: 8px;
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

.role-badge {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 4px;
  padding: 1px 6px;
  flex-shrink: 0;
}

.item-actions {
  display: flex;
  gap: 2px;
  margin-left: 4px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.checklist-item:hover .item-actions {
  opacity: 1;
}

.expand-btn {
  cursor: pointer;
  color: #94a3b8;
  transition: transform 0.2s ease, color 0.15s ease;
  flex-shrink: 0;
}

.expand-btn:hover {
  color: #0095ff;
}

.expand-btn.expanded {
  transform: rotate(90deg);
  color: #0095ff;
}

.item-description {
  margin-top: 6px;
  margin-left: 28px;
  padding: 8px 12px;
  background: #f8fafc;
  border-left: 3px solid #0095ff;
  border-radius: 0 6px 6px 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.ref-link {
  display: inline-block;
  margin-top: 4px;
  font-size: 12px;
  color: #0095ff;
  text-decoration: none;
}

.ref-link:hover {
  text-decoration: underline;
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

/* Import template dialog */
.import-template-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.import-template-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-label {
  font-size: 14px;
  color: #475569;
  white-space: nowrap;
}

.import-preview {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  max-height: 320px;
  overflow-y: auto;
}

.import-phase {
  margin-bottom: 12px;
}

.import-phase:last-child {
  margin-bottom: 0;
}

.import-phase-title {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.import-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
}

.import-item-row:last-child {
  border-bottom: none;
}

.import-mandatory {
  flex-shrink: 0;
}

.import-item-title {
  flex: 1;
  color: #1e293b;
}

.import-item-role {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.import-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 24px 0;
}

.import-count {
  margin-top: 10px;
  text-align: right;
  font-size: 12px;
  color: #64748b;
}

/* frappe-gantt global override (scoped doesn't apply to library DOM) */
:deep(.gantt-container) svg {
  font-family: inherit;
}
</style>
