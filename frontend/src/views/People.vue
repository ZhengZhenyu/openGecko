<template>
  <div class="people-page">
    <!-- Page Title -->
    <div class="page-title-row">
      <div>
        <h2>人脉管理</h2>
        <p class="subtitle">社区贡献者档案与角色关系管理</p>
      </div>
      <div class="title-actions">
        <el-button @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button @click="openImportDialog">
          <el-icon><Upload /></el-icon>导入 Excel
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>新建人脉
        </el-button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="section-card filter-card">
      <el-row :gutter="12" align="middle">
        <el-col :span="8">
          <el-input
            v-model="filters.q"
            placeholder="搜索姓名、邮箱、GitHub"
            clearable
            @keyup.enter="doSearch"
            @clear="doSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="5">
          <el-input
            v-model="filters.company"
            placeholder="公司/组织"
            clearable
            @keyup.enter="doSearch"
            @clear="doSearch"
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.source" placeholder="来源" clearable @change="doSearch">
            <el-option label="手动录入" value="manual" />
            <el-option label="活动导入" value="event_import" />
            <el-option label="GitHub 同步" value="github" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="doSearch">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
        <el-col :span="3" style="text-align: right;">
          <span class="total-hint">共 {{ pagination.total }} 条</span>
        </el-col>
      </el-row>
    </div>

    <!-- Table -->
    <div class="section-card">
      <el-table
        v-loading="loading"
        :data="people"
        row-key="id"
        style="width: 100%"
        @row-click="goDetail"
      >
        <el-table-column label="姓名 / 账号" min-width="200">
          <template #default="{ row }">
            <div class="person-cell">
              <el-avatar
                :size="32"
                :src="row.avatar_url ?? ''"
                :style="{ background: '#eff6ff', color: '#1d4ed8', flexShrink: '0' }"
              >
                {{ row.display_name.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="person-info">
                <span class="person-name">{{ row.display_name }}</span>
                <span v-if="row.github_handle" class="person-handle">@{{ row.github_handle }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="邮箱" prop="email" min-width="180">
          <template #default="{ row }">
            <span class="cell-secondary">{{ row.email ?? '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="公司 / 组织" prop="company" min-width="150">
          <template #default="{ row }">
            <span class="cell-secondary">{{ row.company ?? '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="来源" width="110">
          <template #default="{ row }">
            <span :class="['source-badge', `source-${row.source}`]">
              {{ sourceLabel[row.source] ?? row.source }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="加入时间" width="130">
          <template #default="{ row }">
            <span class="cell-secondary">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="goDetail(row)">详情</el-button>
            <el-button link type="danger" size="small" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadPeople"
          @size-change="doSearch"
        />
      </div>
    </div>

    <!-- Create Person Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建人脉档案"
      width="520px"
      destroy-on-close
    >
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="姓名" required>
          <el-input v-model="createForm.display_name" placeholder="真实姓名或昵称" />
        </el-form-item>
        <el-form-item label="GitHub">
          <el-input v-model="createForm.github_handle" placeholder="GitHub 用户名" />
        </el-form-item>
        <el-form-item label="GitCode">
          <el-input v-model="createForm.gitcode_handle" placeholder="GitCode 用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="createForm.email" placeholder="work@example.com" />
        </el-form-item>
        <el-form-item label="公司 / 组织">
          <el-input v-model="createForm.company" placeholder="所在公司或开源组织" />
        </el-form-item>
        <el-form-item label="所在地">
          <el-input v-model="createForm.location" placeholder="城市，如：上海" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="createForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            style="width: 100%"
            placeholder="输入后回车添加标签"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Excel Import Dialog -->
    <el-dialog v-model="showImportDialog" title="Excel 批量导入人脉" width="900px" destroy-on-close>
      <div class="import-body">
        <!-- Step indicator -->
        <el-steps :active="importStep" finish-status="success" simple style="margin-bottom:20px">
          <el-step title="上传文件" />
          <el-step title="预览确认" />
          <el-step title="导入完成" />
        </el-steps>

        <!-- Step 0 – Upload -->
        <template v-if="importStep === 0">
          <div class="import-hint">
            <p>文件需包含以下列（「*」为必填）：</p>
            <div class="col-list">
              <span class="col-tag required">姓名*</span>
              <span class="col-tag">GitHub账号</span>
              <span class="col-tag">GitCode账号</span>
              <span class="col-tag">邮箱</span>
              <span class="col-tag">手机</span>
              <span class="col-tag">公司/组织</span>
              <span class="col-tag">所在地</span>
              <span class="col-tag">标签(逗号分隔)</span>
              <span class="col-tag">社区(逗号分隔)</span>
              <span class="col-tag">备注</span>
            </div>
          </div>
          <el-upload
            class="excel-upload"
            drag
            accept=".xlsx,.xls"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleFileChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽 Excel 文件到此处，或 <em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .xlsx / .xls 格式，建议先下载模板填写</div>
            </template>
          </el-upload>
        </template>

        <!-- Step 1 – Preview -->
        <template v-else-if="importStep === 1">
          <div class="preview-header">
            <span>共解析 <strong>{{ importRows.length }}</strong> 行，请确认后导入。</span>
            <el-button size="small" @click="importStep = 0">重新上传</el-button>
          </div>
          <el-table :data="importRows" max-height="360" size="small" border style="width:100%">
            <el-table-column label="姓名" prop="display_name" min-width="90" />
            <el-table-column label="GitHub" prop="github_handle" width="110" />
            <el-table-column label="GitCode" prop="gitcode_handle" width="110" />
            <el-table-column label="邮箱" prop="email" min-width="150" />
            <el-table-column label="公司" prop="company" min-width="100" />
            <el-table-column label="社区" min-width="140">
              <template #default="{ row }">
                <span v-for="c in row.communities" :key="c" class="community-chip">{{ c }}</span>
              </template>
            </el-table-column>
            <el-table-column label="标签" min-width="120">
              <template #default="{ row }">
                <span v-for="t in row.tags" :key="t" class="tag-chip">{{ t }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <span v-if="row._status === 'ok'" class="status-ok">✓ 成功</span>
                <span v-else-if="row._status === 'error'" class="status-err" :title="row._error">✗ 失败</span>
                <span v-else class="status-wait">待导入</span>
              </template>
            </el-table-column>
          </el-table>
        </template>

        <!-- Step 2 – Done -->
        <template v-else>
          <div class="import-done">
            <el-icon class="done-icon"><CircleCheck /></el-icon>
            <p>导入完成：<strong>{{ importSuccess }}</strong> 成功，<strong>{{ importFailed }}</strong> 失败</p>
            <p v-if="importFailed > 0" class="done-tip">失败条目已在预览表格中标红，请检查重复邮箱/GitHub账号后重试。</p>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="showImportDialog = false">{{ importStep === 2 ? '关闭' : '取消' }}</el-button>
        <el-button
          v-if="importStep === 1"
          type="primary"
          :loading="importing"
          @click="handleImport"
        >开始导入 ({{ importRows.length }} 条)</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Download, Upload, UploadFilled, CircleCheck } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { listPeople, createPerson, deletePerson, addPersonRole } from '../api/people'
import type { PersonListOut } from '../api/people'

const router = useRouter()

// ─── State ────────────────────────────────────────────────────────────────────
const loading = ref(false)
const people = ref<PersonListOut[]>([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const filters = reactive({ q: '', company: '', source: '' })

const showCreateDialog = ref(false)
const saving = ref(false)
const createForm = reactive({
  display_name: '',
  github_handle: '',
  gitcode_handle: '',
  email: '',
  company: '',
  location: '',
  tags: [] as string[],
  notes: '',
})

// ─── Import State ─────────────────────────────────────────────────────────────
interface ImportRow {
  display_name: string
  github_handle: string
  gitcode_handle: string
  email: string
  phone: string
  company: string
  location: string
  tags: string[]
  communities: string[]
  notes: string
  _status: 'pending' | 'ok' | 'error'
  _error: string
}

const showImportDialog = ref(false)
const importStep = ref(0)
const importRows = ref<ImportRow[]>([])
const importing = ref(false)
const importSuccess = ref(0)
const importFailed = ref(0)

// ─── Labels ───────────────────────────────────────────────────────────────────
const sourceLabel: Record<string, string> = {
  manual: '手动录入',
  event_import: '活动导入',
  github: 'GitHub',
}

// ─── Load ─────────────────────────────────────────────────────────────────────
async function loadPeople() {
  loading.value = true
  try {
    const res = await listPeople({
      q: filters.q || undefined,
      company: filters.company || undefined,
      source: filters.source || undefined,
      page: pagination.page,
      page_size: pagination.page_size,
    })
    people.value = res.items
    pagination.total = res.total
  } catch {
    ElMessage.error('加载人脉列表失败')
  } finally {
    loading.value = false
  }
}

function doSearch() {
  pagination.page = 1
  loadPeople()
}

function resetFilters() {
  filters.q = ''
  filters.company = ''
  filters.source = ''
  doSearch()
}

// ─── Navigation ───────────────────────────────────────────────────────────────
function goDetail(row: PersonListOut) {
  router.push(`/people/${row.id}`)
}

// ─── Create ───────────────────────────────────────────────────────────────────
function openCreateDialog() {
  Object.assign(createForm, {
    display_name: '', github_handle: '', gitcode_handle: '', email: '',
    company: '', location: '', tags: [], notes: '',
  })
  showCreateDialog.value = true
}

async function handleCreate() {
  if (!createForm.display_name.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }
  saving.value = true
  try {
    const person = await createPerson({
      display_name: createForm.display_name,
      github_handle: createForm.github_handle || null,
      gitcode_handle: createForm.gitcode_handle || null,
      email: createForm.email || null,
      company: createForm.company || null,
      location: createForm.location || null,
      tags: createForm.tags,
      notes: createForm.notes || null,
    })
    showCreateDialog.value = false
    ElMessage.success('人脉档案已创建')
    router.push(`/people/${person.id}`)
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg ?? '创建失败，请检查是否有重复的 GitHub 账号或邮箱')
  } finally {
    saving.value = false
  }
}

// ─── Excel Import ─────────────────────────────────────────────────────────────
const TEMPLATE_COLS = [
  '姓名*', 'GitHub账号', 'GitCode账号', '邮箱', '手机',
  '公司/组织', '所在地', '标签(逗号分隔)', '社区(逗号分隔)', '备注'
]

function downloadTemplate() {
  const ws = XLSX.utils.aoa_to_sheet([
    TEMPLATE_COLS,
    ['张三', 'zhangsan', 'zhangsan-gc', 'zhangsan@example.com', '',
     'openEuler', '上海', '内核,安全', 'openEuler,MindSpore', '核心贡献者'],
  ])
  // Set column widths
  ws['!cols'] = TEMPLATE_COLS.map(c => ({ wch: Math.max(c.length * 2, 14) }))
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '人脉模板')
  XLSX.writeFile(wb, '人脉档案导入模板.xlsx')
}

function openImportDialog() {
  importStep.value = 0
  importRows.value = []
  importSuccess.value = 0
  importFailed.value = 0
  showImportDialog.value = true
}

function handleFileChange(file: { raw: File }) {
  const raw = file.raw
  if (!raw) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target!.result as ArrayBuffer)
      const wb = XLSX.read(data, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const rows: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
      if (rows.length < 2) { ElMessage.warning('文件内容为空'); return }

      // Find header row (first row)
      const headers = (rows[0] as string[]).map(h => String(h).trim())
      const idx = (name: string) => {
        const aliases: Record<string, string[]> = {
          display_name: ['姓名*', '姓名', 'display_name', 'name'],
          github_handle: ['GitHub账号', 'github', 'github_handle', 'GitHub'],
          gitcode_handle: ['GitCode账号', 'gitcode', 'gitcode_handle', 'GitCode'],
          email: ['邮箱', 'email'],
          phone: ['手机', 'phone', '电话'],
          company: ['公司/组织', '公司', 'company'],
          location: ['所在地', 'location', '城市'],
          tags: ['标签(逗号分隔)', '标签', 'tags'],
          communities: ['社区(逗号分隔)', '社区', 'communities'],
          notes: ['备注', 'notes'],
        }
        const list = aliases[name] ?? [name]
        for (const a of list) {
          const i = headers.findIndex(h => h === a)
          if (i !== -1) return i
        }
        return -1
      }

      const parsed: ImportRow[] = []
      for (let r = 1; r < rows.length; r++) {
        const row = rows[r] as string[]
        const get = (field: string) => String(row[idx(field)] ?? '').trim()
        const name = get('display_name')
        if (!name) continue
        const tags = get('tags').split(',').map(s => s.trim()).filter(Boolean)
        const communities = get('communities').split(',').map(s => s.trim()).filter(Boolean)
        parsed.push({
          display_name: name,
          github_handle: get('github_handle'),
          gitcode_handle: get('gitcode_handle'),
          email: get('email'),
          phone: get('phone'),
          company: get('company'),
          location: get('location'),
          tags,
          communities,
          notes: get('notes'),
          _status: 'pending',
          _error: '',
        })
      }

      if (parsed.length === 0) { ElMessage.warning('未找到有效数据行（姓名列不可为空）'); return }
      importRows.value = parsed
      importStep.value = 1
    } catch {
      ElMessage.error('文件解析失败，请确认为 Excel 格式')
    }
  }
  reader.readAsArrayBuffer(raw)
}

async function handleImport() {
  importing.value = true
  let ok = 0
  let fail = 0
  for (const row of importRows.value) {
    try {
      const person = await createPerson({
        display_name: row.display_name,
        github_handle: row.github_handle || null,
        gitcode_handle: row.gitcode_handle || null,
        email: row.email || null,
        phone: row.phone || null,
        company: row.company || null,
        location: row.location || null,
        tags: row.tags,
        notes: row.notes || null,
        source: 'event_import',
      })
      // Add community roles
      for (const communityName of row.communities) {
        try {
          await addPersonRole(person.id, {
            community_name: communityName,
            role: 'member',
            is_current: true,
          })
        } catch { /* community role failure is non-fatal */ }
      }
      row._status = 'ok'
      ok++
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      row._status = 'error'
      row._error = msg ?? '未知错误'
      fail++
    }
  }
  importSuccess.value = ok
  importFailed.value = fail
  importing.value = false
  importStep.value = 2
  if (ok > 0) loadPeople()
}

// ─── Delete ───────────────────────────────────────────────────────────────────
async function handleDelete(row: PersonListOut) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.display_name}」的档案？此操作不可撤销。`, '删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
    await deletePerson(row.id)
    ElMessage.success('已删除')
    await loadPeople()
  } catch { /* cancelled */ }
}

// ─── Utils ────────────────────────────────────────────────────────────────────
function formatDate(dt: string): string {
  return new Date(dt).toLocaleDateString('zh-CN')
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => loadPeople())
</script>

<style scoped>
.people-page {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page Title */
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

/* Cards */
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}
.section-card:hover {
  box-shadow: var(--shadow-hover);
}
.filter-card {
  padding: 16px 24px;
}

/* Table */
:deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
}
:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* Person cell */
.person-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.person-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.person-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.person-handle {
  font-size: 12px;
  color: var(--text-muted);
}
.cell-secondary {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Source badge */
.source-badge {
  display: inline-block;
  font-size: 12px;
  border-radius: 6px;
  padding: 2px 8px;
  font-weight: 500;
}
.source-manual  { background: #f1f5f9; color: #64748b; }
.source-event_import { background: #fffbeb; color: #b45309; }
.source-github  { background: #eff6ff; color: #1d4ed8; }

/* Pagination */
.pagination-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}

/* Total hint */
.total-hint {
  font-size: 13px;
  color: var(--text-muted);
}

/* Inputs / Buttons */
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
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
:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}
:deep(.el-button--default:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

/* Dialog */
:deep(.el-dialog) { border-radius: var(--radius); }
:deep(.el-dialog__header) { border-bottom: 1px solid #f1f5f9; }

/* Title actions */
.title-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Import dialog */
.import-body { min-height: 200px; }
.import-hint { margin-bottom: 16px; font-size: 13px; color: var(--text-secondary); }
.import-hint p { margin: 0 0 8px; }
.col-list { display: flex; flex-wrap: wrap; gap: 6px; }
.col-tag {
  display: inline-block;
  font-size: 12px;
  border-radius: 6px;
  padding: 2px 8px;
  background: #f1f5f9;
  color: #64748b;
}
.col-tag.required { background: #fef2f2; color: #dc2626; }

.excel-upload {
  width: 100%;
}
:deep(.excel-upload .el-upload-dragger) {
  width: 100%;
  border-radius: 10px;
  border-color: var(--border);
  background: #f8fafc;
}

/* Preview */
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}
.community-chip, .tag-chip {
  display: inline-block;
  font-size: 11px;
  border-radius: 4px;
  padding: 1px 6px;
  margin: 1px 2px;
}
.community-chip { background: #eff6ff; color: #1d4ed8; }
.tag-chip { background: #f0fdf4; color: #15803d; }

/* Status cells */
.status-ok  { color: #22c55e; font-size: 12px; font-weight: 500; }
.status-err { color: #ef4444; font-size: 12px; font-weight: 500; cursor: help; }
.status-wait { color: #94a3b8; font-size: 12px; }

/* Done */
.import-done {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 0;
  text-align: center;
}
.done-icon { font-size: 56px; color: #22c55e; }
.import-done p { margin: 0; font-size: 15px; color: var(--text-primary); }
.done-tip { font-size: 13px; color: var(--text-muted) !important; }

/* Responsive */
@media (max-width: 1200px) {
  .people-page { padding: 28px 24px; }
}
@media (max-width: 734px) {
  .people-page { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
  .title-actions { flex-wrap: wrap; }
}
</style>
