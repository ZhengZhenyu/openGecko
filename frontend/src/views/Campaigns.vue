<template>
  <div class="campaigns-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">运营活动</h1>
        <p class="page-subtitle">Campaign 策划、联系人漏斗与跟进管理</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        创建运营活动
      </el-button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-select v-model="filterType" placeholder="类型" clearable style="width: 160px" @change="loadCampaigns">
        <el-option-group label="新版活动类型">
          <el-option label="默认活动" value="default" />
          <el-option label="社区成员关怀" value="community_care" />
          <el-option label="开发者关怀" value="developer_care" />
        </el-option-group>
        <el-option-group label="其他">
          <el-option label="推广宣传" value="promotion" />
          <el-option label="关怀回访" value="care" />
          <el-option label="邀请加入" value="invitation" />
          <el-option label="问卷调研" value="survey" />
        </el-option-group>
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" @change="loadCampaigns">
        <el-option label="进行中" value="active" />
        <el-option label="已完成" value="completed" />
      </el-select>
    </div>

    <!-- Campaign List -->
    <div v-loading="loading" class="campaign-grid">
      <div v-if="!loading && campaigns.length === 0" class="empty-state">
        <el-icon class="empty-icon"><MagicStick /></el-icon>
        <p>暂无运营活动，点击右上角创建</p>
      </div>

      <div
        v-for="c in campaigns"
        :key="c.id"
        class="campaign-card"
        @click="$router.push(`/campaigns/${c.id}`)"
      >
        <div class="card-header">
          <el-tag :type="typeTagMap[c.type] ?? 'info'" size="small">{{ typeLabel[c.type] ?? c.type }}</el-tag>
          <el-tag :type="statusTagMap[c.status] ?? 'info'" size="small">{{ statusLabel[c.status] ?? c.status }}</el-tag>
          <el-button
            link
            size="small"
            type="danger"
            style="margin-left: auto"
            @click.stop="confirmDelete(c)"
          >删除</el-button>
        </div>
        <h3 class="campaign-name">{{ c.name }}</h3>
        <p v-if="typeDesc[c.type]" class="campaign-type-desc">{{ typeDesc[c.type] }}</p>
        <div class="campaign-meta">
          <span v-if="c.start_date"><el-icon><Calendar /></el-icon> {{ c.start_date }}</span>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建运营活动" width="560px" destroy-on-close>
      <!-- Step 1: 选择类型 -->
      <template v-if="createStep === 1">
        <p class="create-step-hint">请选择本次运营活动的类型</p>
        <div class="type-selector">
          <div
            v-for="t in typeOptions"
            :key="t.value"
            class="type-option"
            :class="{ 'type-option--active': createForm.type === t.value }"
            @click="createForm.type = t.value"
          >
            <div class="type-option-icon">{{ t.icon }}</div>
            <div class="type-option-body">
              <span class="type-option-label">{{ t.label }}</span>
              <span class="type-option-desc">{{ t.desc }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- Step 2: 填写基本信息 -->
      <template v-else>
        <div class="step2-type-badge">
          <el-tag type="primary" size="small">{{ typeLabel[createForm.type] ?? createForm.type }}</el-tag>
        </div>
        <el-form :model="createForm" label-width="90px">
          <el-form-item label="活动名称" required>
            <el-input v-model="createForm.name" placeholder="请输入运营活动名称" />
          </el-form-item>
          <el-form-item label="关联社区" :required="createForm.type === 'community_care'">
            <el-select v-model="createForm.community_id" placeholder="选择关联社区" clearable style="width: 100%">
              <el-option v-for="c in communities" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <div v-if="createForm.type === 'community_care'" class="field-hint">社区成员关怀必须关联社区，以便从委员会导入成员</div>
          </el-form-item>
          <el-form-item label="开始日期">
            <el-date-picker v-model="createForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker v-model="createForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="活动背景、目标说明等" />
          </el-form-item>
        </el-form>
      </template>

      <template #footer>
        <template v-if="createStep === 1">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createStep = 2">下一步</el-button>
        </template>
        <template v-else>
          <el-button @click="createStep = 1">上一步</el-button>
          <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Plus, User, Calendar } from '@element-plus/icons-vue'
import { listCampaigns, createCampaign, deleteCampaign } from '../api/campaign'
import type { CampaignListItem, CampaignType } from '../api/campaign'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const communities = computed(() => authStore.communities)

const loading = ref(false)
const creating = ref(false)
const campaigns = ref<CampaignListItem[]>([])
const filterType = ref<string>('')
const filterStatus = ref<string>('')
const showCreateDialog = ref(false)
const createStep = ref(1)

const createForm = ref({
  name: '',
  type: 'default' as CampaignType,
  community_id: null as number | null,
  start_date: null as string | null,
  end_date: null as string | null,
  description: '',
})

// ─── 类型配置 ──────────────────────────────────────────────────────────────────

const typeOptions = [
  {
    value: 'default' as CampaignType,
    label: '默认活动',
    icon: '📋',
    desc: '记录工作量、时间、负责人。如节日海报推送、日常宣传任务等',
  },
  {
    value: 'community_care' as CampaignType,
    label: '社区成员关怀',
    icon: '🤝',
    desc: '对委员会委员等核心成员的关怀活动，可从委员会直接导入人员',
  },
  {
    value: 'developer_care' as CampaignType,
    label: '开发者关怀',
    icon: '💻',
    desc: '面向大量开发者的关怀活动，通过 Excel/CSV 批量导入目标人员',
  },
]

const typeLabel: Record<string, string> = {
  default: '默认活动',
  community_care: '社区关怀',
  developer_care: '开发者关怀',
  promotion: '推广宣传',
  care: '关怀回访',
  invitation: '邀请加入',
  survey: '问卷调研',
}

const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  default: 'info',
  community_care: 'success',
  developer_care: 'primary',
  promotion: 'primary',
  care: 'success',
  invitation: 'warning',
  survey: 'info',
}

const typeDesc: Record<string, string> = {
  default: '工作量记录',
  community_care: '委员会成员关怀',
  developer_care: '批量开发者关怀',
  promotion: '推广宣传',
  care: '关怀回访',
  invitation: '邀请加入',
  survey: '问卷调研',
}

const statusLabel: Record<string, string> = { active: '进行中', completed: '已完成' }
const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  active: 'primary', completed: 'success',
}

// ─── 数据加载 ──────────────────────────────────────────────────────────────────

async function loadCampaigns() {
  loading.value = true
  try {
    campaigns.value = await listCampaigns({
      type: filterType.value || undefined,
      status: filterStatus.value || undefined,
    })
  } catch {
    // 错误已由 API 拦截器统一展示
  } finally {
    loading.value = false
  }
}

// ─── 创建对话框 ────────────────────────────────────────────────────────────────

function openCreateDialog() {
  createForm.value = {
    name: '',
    type: 'default',
    community_id: null,
    start_date: null,
    end_date: null,
    description: '',
  }
  createStep.value = 1
  showCreateDialog.value = true
}

async function handleCreate() {
  if (!createForm.value.name.trim()) { ElMessage.warning('请输入活动名称'); return }
  if (createForm.value.type === 'community_care' && !createForm.value.community_id) {
    ElMessage.warning('社区成员关怀活动必须关联一个社区'); return
  }
  creating.value = true
  try {
    const c = await createCampaign({
      name: createForm.value.name,
      type: createForm.value.type,
      community_id: createForm.value.community_id || null,
      start_date: createForm.value.start_date || null,
      end_date: createForm.value.end_date || null,
      description: createForm.value.description || null,
    })
    showCreateDialog.value = false
    ElMessage.success('运营活动已创建')
    router.push(`/campaigns/${c.id}`)
  } catch {
    ElMessage.error('创建失败，请重试')
  } finally {
    creating.value = false
  }
}

onMounted(loadCampaigns)

async function confirmDelete(c: CampaignListItem) {
  try {
    await ElMessageBox.confirm(
      `将彺久删除运营活动「${c.name}」及其所有联系人、任务和跟进记录。此操作不可撤销！`,
      '危险操作 — 删除运营活动',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error', confirmButtonClass: 'el-button--danger' },
    )
    await deleteCampaign(c.id)
    ElMessage.success('已删除')
    loadCampaigns()
  } catch {
    // 用户取消或删除失败
  }
}
</script>

<style scoped>
.campaigns-page {
  padding: 24px 32px;
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
}

.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.campaign-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  min-height: 120px;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px;
  color: #94a3b8;
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
  color: #cbd5e1;
}

.campaign-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.campaign-card:hover {
  border-color: #0095ff;
  box-shadow: 0 4px 16px rgba(0, 149, 255, 0.12);
}

.card-header {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.campaign-name {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.campaign-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
}

.campaign-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.campaign-type-desc {
  margin: 0 0 8px;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
}

/* ─── 类型选择器 ─── */
.create-step-hint {
  margin: 0 0 16px;
  font-size: 14px;
  color: #64748b;
}

.type-selector {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.type-option {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.type-option:hover {
  border-color: #0095ff;
  background: #f8fafc;
}

.type-option--active {
  border-color: #0095ff;
  background: #eff6ff;
}

.type-option-icon {
  font-size: 22px;
  line-height: 1;
  margin-top: 1px;
}

.type-option-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.type-option-label {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.type-option-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.4;
}

/* ─── Step 2 类型徽标 ─── */
.step2-type-badge {
  margin-bottom: 16px;
}

/* ─── 字段提示 ─── */
.field-hint {
  font-size: 11px;
  color: #f59e0b;
  margin-top: 4px;
}
</style>
