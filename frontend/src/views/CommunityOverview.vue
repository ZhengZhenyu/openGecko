<template>
  <div class="community-overview">
    <!-- 页面标题 -->
    <div class="page-title-row">
      <div class="page-title">
        <h2>社区总览</h2>
        <p class="subtitle">查看所有社区的运营概况</p>
      </div>
      <div style="display:flex;gap:10px">
        <el-button v-if="isSuperuser" type="primary" :icon="Plus" @click="showWizard = true">
          创建社区
        </el-button>
        <el-button v-if="isSuperuser" :icon="Setting" @click="$router.push('/communities')">
          管理社区
        </el-button>
      </div>
    </div>
    <!-- 创建社区向导 -->
    <CommunityWizard v-if="showWizard" @completed="handleWizardCompleted" />

    <!-- 指标卡片 -->
    <div class="metric-cards">
      <div class="metric-card">
        <div class="metric-value">{{ totalCommunities }}</div>
        <div class="metric-label">社区总数</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">{{ totalContents }}</div>
        <div class="metric-label">内容总数</div>
      </div>
      <div class="metric-card highlight-warning">
        <div class="metric-value">{{ totalCommittees }}</div>
        <div class="metric-label">委员会总数</div>
      </div>
      <div class="metric-card highlight-success">
        <div class="metric-value">{{ totalPublishes }}</div>
        <div class="metric-label">发布总数</div>
      </div>
    </div>

    <!-- 社区表格 -->
    <div class="section-card">
      <div class="section-header">
        <h3>社区列表</h3>
        <el-input
          v-model="searchQuery"
          placeholder="搜索社区名称或标识"
          :prefix-icon="Search"
          style="width: 280px"
          clearable
        />
      </div>

      <el-table :data="filteredCommunities" style="width: 100%" v-loading="loading">
        <el-table-column label="社区" width="300">
          <template #default="{ row }">
            <div class="community-cell">
              <div class="community-avatar">{{ row.name.charAt(0).toUpperCase() }}</div>
              <div class="community-info">
                <div class="community-name">
                  {{ row.name }}
                  <span v-if="!row.is_active" class="status-badge status-disabled">已停用</span>
                </div>
                <div class="community-slug">{{ row.slug }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="委员会" width="100" align="center">
          <template #default="{ row }">
            <span
              class="count-link"
              :class="{ disabled: row.committee_count === 0 }"
              @click="row.committee_count > 0 && viewCommittees(row.id)"
            >
              {{ row.committee_count || 0 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="内容数" width="100" align="center">
          <template #default="{ row }">
            <span class="meta-text">{{ row.content_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="发布渠道" width="220">
          <template #default="{ row }">
            <div class="channels">
              <span
                v-for="channel in row.channels"
                :key="channel.channel"
                class="count-badge"
                :class="channel.enabled ? 'channel-active' : 'channel-inactive'"
              >
                {{ getChannelLabel(channel.channel) }} ({{ channel.publish_count || 0 }})
              </span>
              <span v-if="!row.channels || row.channels.length === 0" class="empty-text">未配置</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="250">
          <template #default="{ row }">
            <span class="description">{{ row.description || '暂无描述' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewCommunity(row.id)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button
              v-if="canManageCommunity(row)"
              size="small"
              @click="manageCommunity(row.id)"
            >
              <el-icon><Setting /></el-icon>
              管理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, Search, View, Setting
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { getCommunities } from '../api/community'
import type { Community } from '../stores/auth'
import apiClient from '../api/index'
import CommunityWizard from './CommunityWizard.vue'

const showWizard = ref(false)
function handleWizardCompleted(cid: number) {
  showWizard.value = false
  loadCommunities()
}

interface CommunityStats extends Community {
  committee_count?: number
  content_count?: number
  channels?: Array<{
    channel: string
    enabled: boolean
    publish_count?: number
  }>
}

const router = useRouter()
const authStore = useAuthStore()
const isSuperuser = computed(() => authStore.isSuperuser)

const loading = ref(false)
const searchQuery = ref('')
const communities = ref<CommunityStats[]>([])

const filteredCommunities = computed(() => {
  if (!searchQuery.value) return communities.value
  const query = searchQuery.value.toLowerCase()
  return communities.value.filter(c =>
    c.name.toLowerCase().includes(query) ||
    c.slug.toLowerCase().includes(query)
  )
})

const totalCommunities = computed(() => communities.value.length)
const totalCommittees = computed(() =>
  communities.value.reduce((sum, c) => sum + (c.committee_count || 0), 0)
)
const totalContents = computed(() =>
  communities.value.reduce((sum, c) => sum + (c.content_count || 0), 0)
)
const totalPublishes = computed(() => {
  let total = 0
  communities.value.forEach(c => {
    c.channels?.forEach(ch => {
      total += ch.publish_count || 0
    })
  })
  return total
})

const channelLabelMap: Record<string, string> = {
  wechat: '微信',
  hugo: 'Hugo',
  csdn: 'CSDN',
  zhihu: '知乎',
}

function getChannelLabel(channel: string): string {
  return channelLabelMap[channel] || channel
}

function canManageCommunity(community: Community): boolean {
  if (isSuperuser.value) return true
  return community.role === 'admin'
}

function viewCommunity(communityId: number) {
  const community = communities.value.find(c => c.id === communityId)
  if (community) {
    localStorage.setItem('current_community_id', String(communityId))
    router.push('/governance')
  }
}

function viewCommittees(communityId: number) {
  router.push(`/committees?community=${communityId}`)
}

function manageCommunity(communityId: number) {
  router.push('/communities')
}

async function loadCommunities() {
  loading.value = true
  try {
    const communityList = await getCommunities()

    const statsPromises = communityList.map(async (community) => {
      try {
        const committeesRes = await apiClient.get(
          '/committees',
          { headers: { 'X-Community-Id': community.id } }
        )
        const committee_count = committeesRes.data?.length || 0

        const contentsRes = await apiClient.get(
          '/contents',
          { headers: { 'X-Community-Id': community.id } }
        )
        const content_count = contentsRes.data?.length || 0

        const channelsRes = await apiClient.get(
          '/channels',
          { headers: { 'X-Community-Id': community.id } }
        )
        const channels = channelsRes.data || []

        const channelsWithCounts = await Promise.all(
          channels.map(async (channel: any) => {
            try {
              const publishRes = await apiClient.get(
                '/publish/records',
                {
                  params: { channel: channel.channel },
                  headers: { 'X-Community-Id': community.id }
                }
              )
              return {
                ...channel,
                publish_count: publishRes.data?.length || 0
              }
            } catch {
              return { ...channel, publish_count: 0 }
            }
          })
        )

        return {
          ...community,
          committee_count,
          content_count,
          channels: channelsWithCounts
        }
      } catch (error) {
        console.error(`Failed to load stats for community ${community.id}:`, error)
        return {
          ...community,
          committee_count: 0,
          content_count: 0,
          channels: []
        }
      }
    })

    communities.value = await Promise.all(statsPromises)
  } catch (error: any) {
    ElMessage.error(error.message || '加载社区列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCommunities()
})
</script>

<style scoped>
/* LFX Insights Light Theme - Community Overview */
.community-overview {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 0 40px;
  max-width: 1440px;
  margin: 0 auto;
  box-sizing: border-box;
}

/* Page Title Row */
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 32px 0 24px;
}

.page-title {
  display: flex;
  flex-direction: column;
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
  font-size: 15px;
  color: var(--text-secondary);
}

.page-title-row :deep(.el-button) {
  height: 40px;
  padding: 0 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  background: var(--blue);
  border: none;
  color: #fff;
  transition: all 0.15s ease;
}

.page-title-row :deep(.el-button:hover) {
  background: #0080e6;
}

/* Metric Cards */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-bottom: 32px;
}

.metric-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.metric-card:hover {
  box-shadow: var(--shadow-hover);
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 6px;
}

.metric-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.metric-card.highlight-warning .metric-value {
  color: var(--orange);
}

.metric-card.highlight-success .metric-value {
  color: var(--green);
}

/* Section Card */
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.section-card:hover {
  box-shadow: var(--shadow-hover);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-header :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px var(--border);
}

.section-header :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

.section-header :deep(.el-input__inner) {
  font-size: 14px;
  color: var(--text-primary);
}

.section-header :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

/* Table */
.section-card :deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  color: var(--text-primary);
}

.section-card :deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
  padding: 14px 0;
}

.section-card :deep(.el-table td) {
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid #f1f5f9;
  padding: 14px 0;
}

.section-card :deep(.el-table__row:hover) {
  background: #f8fafc;
}

.section-card :deep(.el-button) {
  height: 32px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: #ffffff;
  color: var(--text-primary);
  transition: all 0.15s ease;
}

.section-card :deep(.el-button:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

/* Community Cell */
.community-cell {
  display: flex;
  align-items: center;
  gap: 14px;
}

.community-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--blue), #0080e6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.community-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.community-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.community-slug {
  font-size: 13px;
  color: var(--text-muted);
}

/* Count Link */
.count-link {
  font-size: 14px;
  font-weight: 600;
  color: var(--blue);
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 4px 8px;
  border-radius: 6px;
}

.count-link:hover {
  background: #eff6ff;
}

.count-link.disabled {
  color: var(--text-muted);
  cursor: default;
}

.count-link.disabled:hover {
  background: transparent;
}

/* Badges */
.count-badge {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
  margin-right: 6px;
  margin-bottom: 6px;
}

.channel-active {
  background: #f0fdf4;
  color: #15803d;
}

.channel-inactive {
  background: #f1f5f9;
  color: var(--text-muted);
}

.status-badge {
  display: inline-block;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.status-disabled {
  background: #fef2f2;
  color: var(--red);
}

/* Meta Text */
.meta-text {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.empty-text {
  color: var(--text-muted);
  font-size: 13px;
  font-style: italic;
}

.description {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.channels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* Responsive */
@media (max-width: 1200px) {
  .community-overview {
    padding: 0 24px;
  }

  .page-title-row {
    padding-top: 28px;
    padding-bottom: 20px;
  }

  .metric-cards {
    padding-bottom: 24px;
  }
}

@media (max-width: 1024px) {
  .metric-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 734px) {
  .community-overview {
    padding: 0 16px;
  }

  .page-title-row {
    flex-direction: column;
    gap: 16px;
    padding-top: 24px;
    padding-bottom: 16px;
  }

  .page-title h2 {
    font-size: 22px;
  }

  .metric-cards {
    grid-template-columns: 1fr;
    padding-bottom: 16px;
  }

  .section-card {
    padding: 20px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .section-header :deep(.el-input) {
    width: 100% !important;
  }
}
</style>
