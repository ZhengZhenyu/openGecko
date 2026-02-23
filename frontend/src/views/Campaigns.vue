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
      <el-select v-model="filterType" placeholder="类型" clearable style="width: 130px" @change="loadCampaigns">
        <el-option label="推广宣传" value="promotion" />
        <el-option label="关怀回访" value="care" />
        <el-option label="邀请加入" value="invitation" />
        <el-option label="问卷调研" value="survey" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" @change="loadCampaigns">
        <el-option label="草稿" value="draft" />
        <el-option label="进行中" value="active" />
        <el-option label="已完成" value="completed" />
        <el-option label="已归档" value="archived" />
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
        </div>
        <h3 class="campaign-name">{{ c.name }}</h3>
        <div class="campaign-meta">
          <span v-if="c.target_count"><el-icon><User /></el-icon> 目标 {{ c.target_count }} 人</span>
          <span v-if="c.start_date"><el-icon><Calendar /></el-icon> {{ c.start_date }}</span>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建运营活动" width="480px" destroy-on-close>
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="活动名称" required>
          <el-input v-model="createForm.name" placeholder="请输入运营活动名称" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="createForm.type" style="width: 100%">
            <el-option label="推广宣传" value="promotion" />
            <el-option label="关怀回访" value="care" />
            <el-option label="邀请加入" value="invitation" />
            <el-option label="问卷调研" value="survey" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标人数">
          <el-input-number v-model="createForm.target_count" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="createForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="createForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="关联社区">
          <el-select v-model="createForm.community_id" placeholder="可选，关联到某社区" clearable style="width: 100%">
            <el-option v-for="c in communities" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick, Plus, User, Calendar } from '@element-plus/icons-vue'
import { listCampaigns, createCampaign } from '../api/campaign'
import type { CampaignListItem } from '../api/campaign'
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

const createForm = ref({
  name: '',
  type: 'promotion',
  community_id: null as number | null,
  target_count: null as number | null,
  start_date: null as string | null,
  end_date: null as string | null,
  description: '',
})

const typeLabel: Record<string, string> = { promotion: '推广宣传', care: '关怀回访', invitation: '邀请加入', survey: '问卷调研' }
const typeTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { promotion: 'primary', care: 'success', invitation: 'warning', survey: 'info' }
const statusLabel: Record<string, string> = { draft: '草稿', active: '进行中', completed: '已完成', archived: '已归档' }
const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = { draft: 'info', active: 'primary', completed: 'success', archived: '' }

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

function openCreateDialog() {
  createForm.value = { name: '', type: 'promotion', community_id: null, target_count: null, start_date: null, end_date: null, description: '' }
  showCreateDialog.value = true
}

async function handleCreate() {
  if (!createForm.value.name.trim()) { ElMessage.warning('请输入活动名称'); return }
  creating.value = true
  try {
    const c = await createCampaign({
      name: createForm.value.name,
      type: createForm.value.type,
      community_id: createForm.value.community_id || null,
      target_count: createForm.value.target_count || null,
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
</style>
