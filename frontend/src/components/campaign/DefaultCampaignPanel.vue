<template>
  <div class="default-panel">
    <!-- 任务规划卡 -->
    <div class="section-card">
      <div class="section-header">
        <div>
          <h3 class="section-title">📋 任务规划</h3>
          <p class="section-hint">创建任务、指定负责人和目标完成时间，纳入个人工作台统一追踪。</p>
        </div>
        <el-button type="primary" size="small" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新增任务
        </el-button>
      </div>

      <!-- 任务列表 -->
      <el-table v-loading="loading" :data="tasks" style="width: 100%">
        <el-table-column label="任务名称" min-width="200">
          <template #default="{ row }">
            <span class="task-title">{{ row.title }}</span>
            <span v-if="isOverdue(row)" class="overdue-tag">已逾期</span>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="160">
          <template #default="{ row }">
            <span v-if="row.assignee_ids.length === 0" class="text-muted">—</span>
            <span v-else>{{ resolveAssignees(row.assignee_ids) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <span :class="['priority-tag', `priority-${row.priority}`]">{{ PRIORITY_LABELS[row.priority] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <span :class="['status-tag', `status-${row.status}`]">{{ STATUS_LABELS[row.status] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="120">
          <template #default="{ row }">{{ row.deadline ?? '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && tasks.length === 0" class="empty-hint">
        暂无任务，点击「新增任务」创建
      </div>
    </div>

    <!-- 创建 / 编辑任务 Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingTask ? '编辑任务' : '新增任务'"
      width="480px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="form.assignee_ids"
            multiple
            filterable
            placeholder="选择负责人（可多选）"
            style="width: 100%"
          >
            <el-option
              v-for="u in communityUsers"
              :key="u.id"
              :label="u.full_name || u.username"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="form.deadline"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择截止日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="未开始" value="not_started" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="阻塞中" value="blocked" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { CampaignDetail, CampaignTaskOut, TaskStatus, TaskPriority } from '../../api/campaign'
import {
  listCampaignTasks,
  createCampaignTask,
  updateCampaignTask,
  deleteCampaignTask,
} from '../../api/campaign'
import { getCommunityUsers } from '../../api/community'
import type { CommunityUser } from '../../api/community'

const props = defineProps<{ campaign: CampaignDetail }>()

// ─── 常量 ──────────────────────────────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
  blocked: '阻塞中',
}
const PRIORITY_LABELS: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

// ─── 数据 ──────────────────────────────────────────────────────────────────────

const loading = ref(false)
const tasks = ref<CampaignTaskOut[]>([])
const communityUsers = ref<CommunityUser[]>([])

async function loadData() {
  loading.value = true
  try {
    const [taskList, users] = await Promise.all([
      listCampaignTasks(props.campaign.id),
      props.campaign.community_id
        ? getCommunityUsers(props.campaign.community_id)
        : Promise.resolve([]),
    ])
    tasks.value = taskList
    communityUsers.value = users
  } catch {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

function resolveAssignees(ids: number[]): string {
  return ids
    .map((id) => {
      const u = communityUsers.value.find((u) => u.id === id)
      return u ? u.full_name || u.username : `#${id}`
    })
    .join('、')
}

function isOverdue(task: CampaignTaskOut): boolean {
  if (!task.deadline || task.status === 'completed') return false
  return task.deadline < new Date().toISOString().slice(0, 10)
}

// ─── 对话框 ────────────────────────────────────────────────────────────────────

const showDialog = ref(false)
const saving = ref(false)
const editingTask = ref<CampaignTaskOut | null>(null)
const formRef = ref<FormInstance>()

const DEFAULT_FORM = () => ({
  title: '',
  description: null as string | null,
  status: 'not_started' as TaskStatus,
  priority: 'medium' as TaskPriority,
  assignee_ids: [] as number[],
  deadline: null as string | null,
})
const form = ref(DEFAULT_FORM())

const formRules: FormRules = {
  title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
}

function openCreateDialog() {
  editingTask.value = null
  form.value = DEFAULT_FORM()
  showDialog.value = true
}

function openEditDialog(task: CampaignTaskOut) {
  editingTask.value = task
  form.value = {
    title: task.title,
    description: task.description,
    status: task.status as TaskStatus,
    priority: task.priority as TaskPriority,
    assignee_ids: [...task.assignee_ids],
    deadline: task.deadline,
  }
  showDialog.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingTask.value) {
      const updated = await updateCampaignTask(props.campaign.id, editingTask.value.id, form.value)
      const idx = tasks.value.findIndex((t) => t.id === updated.id)
      if (idx !== -1) tasks.value[idx] = updated
    } else {
      const created = await createCampaignTask(props.campaign.id, form.value)
      tasks.value.push(created)
    }
    showDialog.value = false
    ElMessage.success(editingTask.value ? '任务已更新' : '任务已创建')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

async function handleDelete(task: CampaignTaskOut) {
  await ElMessageBox.confirm(`确认删除任务「${task.title}」？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  try {
    await deleteCampaignTask(props.campaign.id, task.id)
    tasks.value = tasks.value.filter((t) => t.id !== task.id)
    ElMessage.success('任务已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.default-panel {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --radius: 12px;

  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 16px;
}

.section-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.empty-hint {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}

.task-title {
  font-size: 13px;
  color: var(--text-primary);
}

.overdue-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 11px;
  font-weight: 500;
}

.text-muted {
  color: var(--text-muted);
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}
.status-tag.status-not_started { background: #f1f5f9; color: #64748b; }
.status-tag.status-in_progress { background: #eff6ff; color: #1d4ed8; }
.status-tag.status-completed   { background: #f0fdf4; color: #15803d; }
.status-tag.status-blocked     { background: #fef2f2; color: #dc2626; }

/* 优先级标签 */
.priority-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}
.priority-tag.priority-high   { background: #fef2f2; color: #dc2626; }
.priority-tag.priority-medium { background: #fffbeb; color: #b45309; }
.priority-tag.priority-low    { background: #f0fdf4; color: #15803d; }

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
:deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
}
:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
</style>
