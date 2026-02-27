<template>
  <div v-loading="loading" class="campaign-detail">
    <template v-if="campaign">
      <!-- 返回 -->
      <div class="detail-nav">
        <el-button link @click="$router.push('/campaigns')">
          <el-icon><ArrowLeft /></el-icon> 返回运营活动
        </el-button>
      </div>

      <!-- ═══ 通用头部信息卡 ═══ -->
      <div class="info-card">
        <div class="info-top">
          <div class="info-left">
            <div class="info-title-row">
              <template v-if="!editingInfo">
                <h1 class="campaign-title">{{ campaign.name }}</h1>
                <el-button link size="small" @click="startEditInfo">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </template>
              <template v-else>
                <el-input v-model="editForm.name" style="width: 300px" />
                <el-button type="primary" size="small" :loading="savingInfo" @click="saveInfo">保存</el-button>
                <el-button size="small" @click="editingInfo = false">取消</el-button>
              </template>
            </div>
            <div class="info-badges">
              <el-tag :type="typeTagMap[campaign.type] ?? 'info'" size="small">
                {{ typeLabel[campaign.type] ?? campaign.type }}
              </el-tag>
              <el-tag :type="statusTagMap[campaign.status] ?? 'info'" size="small">
                {{ statusLabel[campaign.status] ?? campaign.status }}
              </el-tag>
              <el-tag v-if="communityName" type="info" size="small">
                {{ communityName }}
              </el-tag>
            </div>
            <template v-if="editingInfo">
              <el-input
                v-model="editForm.description"
                type="textarea"
                :rows="2"
                placeholder="活动描述（可选）"
                style="margin-top: 8px"
              />
            </template>
            <p v-else-if="campaign.description" class="campaign-desc">{{ campaign.description }}</p>
          </div>

          <div class="info-right">
            <div class="meta-grid">
              <div class="meta-item">
                <span class="meta-label">状态</span>
                <el-select
                  v-model="campaign.status"
                  size="small"
                  style="width: 110px"
                  @change="handleStatusChange"
                >
                  <el-option v-for="(lbl, val) in statusLabel" :key="val" :label="lbl" :value="val" />
                </el-select>
              </div>
              <div class="meta-item">
                <span class="meta-label">开始</span>
                <el-date-picker
                  v-if="editingInfo"
                  v-model="editForm.start_date"
                  type="date"
                  value-format="YYYY-MM-DD"
                  size="small"
                  style="width: 140px"
                />
                <span v-else class="meta-value">{{ campaign.start_date ?? '—' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">结束</span>
                <el-date-picker
                  v-if="editingInfo"
                  v-model="editForm.end_date"
                  type="date"
                  value-format="YYYY-MM-DD"
                  size="small"
                  style="width: 140px"
                />
                <span v-else class="meta-value">{{ campaign.end_date ?? '—' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 类型专属面板 ═══ -->

      <!-- 默认活动 -->
      <template v-if="campaign.type === 'default'">
        <DefaultCampaignPanel :campaign="campaign" />
      </template>

      <!-- 社区成员关怀 -->
      <template v-else-if="campaign.type === 'community_care'">
        <CommunityCarePanel :campaign="campaign" @reload="reloadFunnel" />
      </template>

      <!-- 开发者关怀 -->
      <template v-else-if="campaign.type === 'developer_care'">
        <DeveloperCarePanel :campaign="campaign" @reload="reloadFunnel" />
      </template>

      <!-- 旧版类型（通用） -->
      <template v-else>
        <LegacyCampaignPanel
          :campaign="campaign"
          :funnel="funnel"
          @reload="reloadFunnel"
        />
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Edit } from '@element-plus/icons-vue'
import { getCampaign, getCampaignFunnel, updateCampaign } from '../api/campaign'
import type { CampaignDetail, CampaignFunnel } from '../api/campaign'
import { useAuthStore } from '../stores/auth'
import DefaultCampaignPanel from '../components/campaign/DefaultCampaignPanel.vue'
import CommunityCarePanel from '../components/campaign/CommunityCarePanel.vue'
import DeveloperCarePanel from '../components/campaign/DeveloperCarePanel.vue'
import LegacyCampaignPanel from '../components/campaign/LegacyCampaignPanel.vue'

const route = useRoute()
const authStore = useAuthStore()
const campaignId = computed(() => Number(route.params.id))

const communities = computed(() => authStore.communities)
const communityName = computed(() => {
  if (!campaign.value?.community_id) return ''
  return (
    communities.value.find((c) => c.id === campaign.value!.community_id)?.name ??
    `社区#${campaign.value.community_id}`
  )
})

const loading = ref(false)
const campaign = ref<CampaignDetail | null>(null)
const funnel = ref<CampaignFunnel | null>(null)

// ─── 编辑信息 ──────────────────────────────────────────────────────────────────
const editingInfo = ref(false)
const savingInfo = ref(false)
const editForm = ref({
  name: '',
  description: '',
  start_date: null as string | null,
  end_date: null as string | null,
})

function startEditInfo() {
  if (!campaign.value) return
  editForm.value = {
    name: campaign.value.name,
    description: campaign.value.description ?? '',
    start_date: campaign.value.start_date,
    end_date: campaign.value.end_date,
  }
  editingInfo.value = true
}

async function saveInfo() {
  if (!editForm.value.name.trim()) { ElMessage.warning('活动名称不能为空'); return }
  savingInfo.value = true
  try {
    const updated = await updateCampaign(campaignId.value, {
      name: editForm.value.name,
      description: editForm.value.description || null,
      start_date: editForm.value.start_date || null,
      end_date: editForm.value.end_date || null,
    })
    campaign.value = updated
    editingInfo.value = false
    ElMessage.success('信息已更新')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingInfo.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  try {
    await updateCampaign(campaignId.value, { status: newStatus })
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('更新失败')
  }
}

// ─── 类型标签映射 ──────────────────────────────────────────────────────────────
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
const statusLabel: Record<string, string> = {
  draft: '草稿',
  active: '进行中',
  completed: '已完成',
  archived: '已归档',
}
const statusTagMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  draft: 'info',
  active: 'primary',
  completed: 'success',
  archived: '',
}

// ─── 数据加载 ──────────────────────────────────────────────────────────────────
async function reloadFunnel() {
  funnel.value = await getCampaignFunnel(campaignId.value)
}

onMounted(async () => {
  loading.value = true
  try {
    const [c, f] = await Promise.all([
      getCampaign(campaignId.value),
      getCampaignFunnel(campaignId.value),
    ])
    campaign.value = c
    funnel.value = f
  } catch {
    ElMessage.error('加载运营活动失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.campaign-detail {
  padding: 24px 32px 60px;
  max-width: 1280px;
  margin: 0 auto;
}

.detail-nav {
  margin-bottom: 16px;
}

.info-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.info-top {
  display: flex;
  gap: 32px;
  justify-content: space-between;
  align-items: flex-start;
}

.info-left {
  flex: 1;
  min-width: 0;
}

.info-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.campaign-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.info-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.campaign-desc {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
}

.info-right {
  flex-shrink: 0;
  min-width: 200px;
}

.meta-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-label {
  font-size: 12px;
  color: #94a3b8;
  width: 52px;
  flex-shrink: 0;
}

.meta-value {
  font-size: 13px;
  color: #1e293b;
}
</style>
