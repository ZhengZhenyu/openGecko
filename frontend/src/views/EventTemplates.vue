<template>
  <div class="templates-page">
    <!-- Page Header -->
    <div class="page-title-row">
      <div>
        <h2>SOP 模板管理</h2>
        <p class="subtitle">管理活动标准操作流程（SOP）模板，创建活动时可自动生成检查项</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建模板
      </el-button>
    </div>

    <div class="main-layout">
      <!-- Left: Template list -->
      <div class="template-list-col">
        <div v-if="loading" class="list-loading">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="templates.length === 0" class="list-empty">
          暂无模板，点击「新建模板」开始创建
        </div>
        <div
          v-for="t in templates"
          :key="t.id"
          class="template-card"
          :class="{ active: selectedId === t.id }"
          @click="selectTemplate(t.id)"
        >
          <div class="template-card-header">
            <span class="template-name">{{ t.name }}</span>
            <el-tag :type="typeTagMap[t.event_type] ?? 'info'" size="small">{{ typeLabel[t.event_type] ?? t.event_type }}</el-tag>
          </div>
          <div class="template-card-meta">
            <el-tag v-if="t.is_public" type="success" size="small">公开</el-tag>
            <el-tag v-else type="info" size="small">私有</el-tag>
          </div>
        </div>
      </div>

      <!-- Right: Template detail & edit -->
      <div class="template-detail-col">
        <div v-if="!selected" class="detail-empty">
          请从左侧选择一个模板
        </div>
        <template v-else>
          <!-- Basic info -->
          <div class="section-card">
            <div class="section-header">
              <h3>基本信息</h3>
              <div class="header-actions">
                <el-button size="small" type="primary" :loading="savingInfo" @click="saveInfo">保存</el-button>
                <el-button size="small" type="danger" link @click="handleDeleteTemplate">删除模板</el-button>
              </div>
            </div>
            <el-form :model="infoForm" label-width="90px" size="small" style="margin-top:16px">
              <el-form-item label="模板名称">
                <el-input v-model="infoForm.name" />
              </el-form-item>
              <el-form-item label="活动类型">
                <el-select v-model="infoForm.event_type" style="width:100%">
                  <el-option label="线下" value="offline" />
                  <el-option label="线上" value="online" />
                  <el-option label="混合" value="hybrid" />
                </el-select>
              </el-form-item>
              <el-form-item label="描述">
                <el-input v-model="infoForm.description" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item label="是否公开">
                <el-switch v-model="infoForm.is_public" />
                <span style="margin-left:8px;font-size:12px;color:#64748b">公开模板可被所有用户选用</span>
              </el-form-item>
            </el-form>
          </div>

          <!-- Checklist items -->
          <div class="section-card">
            <div class="section-header">
              <h3>检查项（{{ selected.checklist_items.length }} 条）</h3>
              <el-button size="small" type="primary" @click="openAddItemDialog('pre')">
                <el-icon><Plus /></el-icon>添加条目
              </el-button>
            </div>

            <div v-for="phase in phases" :key="phase.key" class="phase-group">
              <div class="phase-title">{{ phase.label }}</div>
              <div v-if="draggableItems[phase.key].length === 0" class="phase-empty">本阶段暂无条目</div>
              <draggable
                v-else
                :list="draggableItems[phase.key]"
                item-key="id"
                handle=".drag-handle"
                ghost-class="drag-ghost"
                :animation="150"
                @end="onDragEnd(phase.key)"
              >
                <template #item="{ element: item }">
                  <div class="item-row">
                    <div class="drag-handle" title="拖拽排序">
                      <span class="drag-dots"></span>
                    </div>
                    <div class="item-content">
                      <div class="item-main">
                        <span class="item-title">{{ item.title }}</span>
                        <el-tag v-if="item.is_mandatory" type="danger" size="small" style="flex-shrink:0">必须</el-tag>
                        <span v-if="item.responsible_role" class="item-role">{{ item.responsible_role }}</span>
                        <span v-if="item.deadline_offset_days !== null && item.deadline_offset_days !== undefined" class="item-offset">
                          {{ item.deadline_offset_days >= 0 ? `活动后 ${item.deadline_offset_days} 天` : `活动前 ${Math.abs(item.deadline_offset_days)} 天` }}
                        </span>
                        <div class="item-actions">
                          <el-button link size="small" @click="openEditItemDialog(item)">编辑</el-button>
                          <el-button link size="small" type="danger" @click="handleDeleteItem(item.id)">删除</el-button>
                        </div>
                      </div>
                      <div v-if="item.description" class="item-desc">{{ item.description }}</div>
                    </div>
                  </div>
                </template>
              </draggable>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Create template dialog -->
    <el-dialog v-model="showCreateDialog" title="新建模板" width="480px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="90px" size="small">
        <el-form-item label="模板名称" required>
          <el-input v-model="createForm.name" placeholder="例：线下技术沙龙 SOP" />
        </el-form-item>
        <el-form-item label="活动类型">
          <el-select v-model="createForm.event_type" style="width:100%">
            <el-option label="线下" value="offline" />
            <el-option label="线上" value="online" />
            <el-option label="混合" value="hybrid" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="createForm.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Add/Edit item dialog -->
    <el-dialog v-model="showItemDialog" :title="editingItem ? '编辑条目' : '添加条目'" width="560px" :close-on-click-modal="false">
      <el-form :model="itemForm" label-width="100px" size="small">
        <el-form-item label="阶段">
          <el-select v-model="itemForm.phase" style="width:100%">
            <el-option label="会前准备" value="pre" />
            <el-option label="会中执行" value="during" />
            <el-option label="会后复盘" value="post" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="itemForm.title" placeholder="例：确认会场预订" />
        </el-form-item>
        <el-form-item label="说明/指导">
          <el-input v-model="itemForm.description" type="textarea" :rows="3"
            placeholder="详细操作说明，帮助执行者理解如何完成此项" />
        </el-form-item>
        <el-form-item label="负责角色">
          <el-input v-model="itemForm.responsible_role" placeholder="例：活动负责人" />
        </el-form-item>
        <el-form-item label="时间偏移（天）">
          <el-input-number v-model="itemForm.deadline_offset_days" :precision="0" style="width:100%" />
          <div style="margin-top:4px;font-size:12px;color:#94a3b8">负值表示活动前 N 天，正值表示活动后 N 天</div>
        </el-form-item>
        <el-form-item label="预估工时（h）">
          <el-input-number v-model="itemForm.estimated_hours" :min="0" :step="0.5" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="参考链接">
          <el-input v-model="itemForm.reference_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="是否必须">
          <el-switch v-model="itemForm.is_mandatory" />
          <span style="margin-left:8px;font-size:12px;color:#64748b">必须项不可被跳过</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showItemDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingItem" @click="handleSaveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {
  listTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  addTemplateItem,
  updateTemplateItem,
  deleteTemplateItem,
} from '../api/event'
import type { EventTemplateListItem, EventTemplate, ChecklistTemplateItem } from '../api/event'

const templates = ref<EventTemplateListItem[]>([])
const selectedId = ref<number | null>(null)
const selected = ref<EventTemplate | null>(null)
const loading = ref(false)

// Info form (synced with selected)
const infoForm = ref({ name: '', event_type: 'offline', description: '', is_public: false })
const savingInfo = ref(false)

// Create dialog
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({ name: '', event_type: 'offline', description: '', is_public: false })

// Item dialog
const showItemDialog = ref(false)
const savingItem = ref(false)
const editingItem = ref<ChecklistTemplateItem | null>(null)
const defaultItemForm = () => ({
  phase: 'pre',
  title: '',
  description: '',
  responsible_role: '',
  deadline_offset_days: null as number | null,
  estimated_hours: null as number | null,
  reference_url: '',
  is_mandatory: false,
})
const itemForm = ref(defaultItemForm())

// Drag-and-drop: mutable per-phase arrays driven by selected template
const draggableItems = ref<Record<string, ChecklistTemplateItem[]>>({ pre: [], during: [], post: [] })

watch(selected, (val) => {
  const items = val?.checklist_items ?? []
  draggableItems.value = {
    pre:    [...items.filter(i => i.phase === 'pre')].sort((a, b) => a.order - b.order),
    during: [...items.filter(i => i.phase === 'during')].sort((a, b) => a.order - b.order),
    post:   [...items.filter(i => i.phase === 'post')].sort((a, b) => a.order - b.order),
  }
})

const typeLabel: Record<string, string> = { offline: '线下', online: '线上', hybrid: '混合' }
const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  offline: '',
  online: 'success',
  hybrid: 'warning',
}
const phases = [
  { key: 'pre' as const, label: '会前准备' },
  { key: 'during' as const, label: '会中执行' },
  { key: 'post' as const, label: '会后复盘' },
]

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await listTemplates()
  } finally {
    loading.value = false
  }
}

async function selectTemplate(id: number) {
  selectedId.value = id
  try {
    selected.value = await getTemplate(id)
    infoForm.value = {
      name: selected.value.name,
      event_type: selected.value.event_type,
      description: selected.value.description ?? '',
      is_public: selected.value.is_public,
    }
  } catch {
    ElMessage.error('加载模板详情失败')
  }
}

async function saveInfo() {
  if (!selected.value) return
  if (!infoForm.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  savingInfo.value = true
  try {
    await updateTemplate(selected.value.id, {
      name: infoForm.value.name,
      event_type: infoForm.value.event_type,
      description: infoForm.value.description || null,
      is_public: infoForm.value.is_public,
    })
    await loadTemplates()
    await selectTemplate(selected.value.id)
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingInfo.value = false
  }
}

async function handleDeleteTemplate() {
  if (!selected.value) return
  await ElMessageBox.confirm('确认删除此模板？删除后不可恢复。', '删除确认', { type: 'warning' })
  try {
    await deleteTemplate(selected.value.id)
    selected.value = null
    selectedId.value = null
    await loadTemplates()
    ElMessage.success('模板已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  creating.value = true
  try {
    const t = await createTemplate({
      name: createForm.value.name,
      event_type: createForm.value.event_type,
      description: createForm.value.description || null,
      is_public: createForm.value.is_public,
    })
    showCreateDialog.value = false
    createForm.value = { name: '', event_type: 'offline', description: '', is_public: false }
    await loadTemplates()
    await selectTemplate(t.id)
    ElMessage.success('模板已创建')
  } catch {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

function openAddItemDialog(phase: string) {
  editingItem.value = null
  itemForm.value = { ...defaultItemForm(), phase }
  showItemDialog.value = true
}

function openEditItemDialog(item: ChecklistTemplateItem) {
  editingItem.value = item
  itemForm.value = {
    phase: item.phase,
    title: item.title,
    description: item.description ?? '',
    responsible_role: item.responsible_role ?? '',
    deadline_offset_days: item.deadline_offset_days,
    estimated_hours: item.estimated_hours,
    reference_url: item.reference_url ?? '',
    is_mandatory: item.is_mandatory,
  }
  showItemDialog.value = true
}

async function handleSaveItem() {
  if (!selected.value) return
  if (!itemForm.value.title.trim()) {
    ElMessage.warning('请输入条目标题')
    return
  }
  savingItem.value = true
  try {
    const phaseItems = draggableItems.value[itemForm.value.phase] ?? []
    const nextOrder = editingItem.value ? editingItem.value.order : phaseItems.length

    const payload = {
      phase: itemForm.value.phase,
      title: itemForm.value.title,
      description: itemForm.value.description || null,
      responsible_role: itemForm.value.responsible_role || null,
      deadline_offset_days: itemForm.value.deadline_offset_days,
      estimated_hours: itemForm.value.estimated_hours,
      reference_url: itemForm.value.reference_url || null,
      is_mandatory: itemForm.value.is_mandatory,
      order: nextOrder,
    }
    if (editingItem.value) {
      await updateTemplateItem(selected.value.id, editingItem.value.id, payload)
    } else {
      await addTemplateItem(selected.value.id, payload)
    }
    showItemDialog.value = false
    await selectTemplate(selected.value.id)
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingItem.value = false
  }
}

async function handleDeleteItem(itemId: number) {
  if (!selected.value) return
  await ElMessageBox.confirm('确认删除此条目？', '删除确认', { type: 'warning' })
  try {
    await deleteTemplateItem(selected.value.id, itemId)
    await selectTemplate(selected.value.id)
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function onDragEnd(phase: 'pre' | 'during' | 'post') {
  if (!selected.value) return
  const items = draggableItems.value[phase]
  // Collect only items whose order actually changed
  const updates = items
    .map((item, index) => ({ item, newOrder: index }))
    .filter(({ item, newOrder }) => item.order !== newOrder)

  if (updates.length === 0) return

  try {
    await Promise.all(
      updates.map(({ item, newOrder }) =>
        updateTemplateItem(selected.value!.id, item.id, { order: newOrder })
      )
    )
    // Silently refresh order values without full UI flicker
    updates.forEach(({ item, newOrder }) => { item.order = newOrder })
    // Also keep selected in sync
    await selectTemplate(selected.value.id)
  } catch {
    ElMessage.error('保存排序失败')
    await selectTemplate(selected.value.id)
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
.templates-page {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;
  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title-row h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
  border-radius: 8px;
  font-weight: 500;
}

:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-button--default) {
  border-radius: 8px;
  font-weight: 500;
}

.main-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  align-items: start;
}

/* ── Template list ── */
.template-list-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-loading,
.list-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

.template-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow);
}

.template-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: #cbd5e1;
}

.template-card.active {
  border-color: var(--blue);
  background: #eff6ff;
}

.template-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-card-meta {
  margin-top: 6px;
}

/* ── Detail col ── */
.template-detail-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-empty {
  background: #fff;
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  padding: 60px 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: 15px;
}

.section-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* ── Checklist items ── */
.phase-group {
  margin-top: 20px;
}

.phase-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.phase-empty {
  font-size: 13px;
  color: var(--text-muted);
  padding: 8px 0;
}

/* ── Drag-and-drop item row ── */
.item-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 9px 0;
  border-bottom: 1px solid #f8fafc;
  border-radius: 6px;
  transition: background 0.1s;
}

.item-row:hover {
  background: #f8fafc;
}

/* Drag handle — six-dot grid */
.drag-handle {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 2px;
  cursor: grab;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.15s;
}

.item-row:hover .drag-handle {
  opacity: 1;
}

.drag-handle:active {
  cursor: grabbing;
}

/* Six dots using a repeating radial-gradient */
.drag-dots {
  display: block;
  width: 10px;
  height: 16px;
  background-image: radial-gradient(circle, currentColor 1.5px, transparent 1.5px);
  background-size: 5px 5px;
  background-repeat: repeat;
  background-position: 0 0;
  color: #94a3b8;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.item-title {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  flex: 1;
  min-width: 120px;
}

.item-role {
  font-size: 12px;
  color: var(--text-secondary);
  background: #f1f5f9;
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

.item-offset {
  font-size: 12px;
  color: #b45309;
  background: #fffbeb;
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

.item-desc {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-secondary);
  padding-left: 4px;
  border-left: 2px solid #e2e8f0;
  line-height: 1.5;
}

.item-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
  flex-shrink: 0;
}

/* Drag ghost placeholder */
.drag-ghost {
  opacity: 0.4;
  background: #eff6ff;
  border-radius: 6px;
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

:deep(.el-dialog__header) {
  border-bottom: 1px solid #f1f5f9;
}

@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 734px) {
  .templates-page {
    padding: 20px 16px;
  }

  .page-title-row h2 {
    font-size: 22px;
  }
}
</style>
