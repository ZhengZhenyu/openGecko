<template>
  <div class="community-overview">
    <div class="page-header">
      <h2>社区总览</h2>
      <el-button v-if="isSuperuser" type="primary" :icon="Plus" @click="$router.push('/communities')">
        管理社区
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#409eff"><OfficeBuilding /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalCommunities }}</div>
              <div class="stat-label">社区总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#67c23a"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalContents }}</div>
              <div class="stat-label">内容总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#e6a23c"><Avatar /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalCommittees }}</div>
              <div class="stat-label">委员会总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="40" color="#f56c6c"><Promotion /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalPublishes }}</div>
              <div class="stat-label">发布总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="communities-card">
      <template #header>
        <div class="card-header">
          <span>社区列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索社区名称或标识"
            :prefix-icon="Search"
            style="width: 300px"
            clearable
          />
        </div>
      </template>

      <el-table :data="filteredCommunities" stripe style="width: 100%" v-loading="loading">
        <el-table-column label="社区" width="300">
          <template #default="{ row }">
            <div class="community-cell">
              <div class="community-name">
                {{ row.name }}
                <el-tag v-if="!row.is_active" type="danger" size="small">已停用</el-tag>
              </div>
              <div class="community-slug">{{ row.slug }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="委员会" width="120" align="center">
          <template #default="{ row }">
            <el-link 
              :underline="false" 
              @click="viewCommittees(row.id)"
              :disabled="row.committee_count === 0"
            >
              {{ row.committee_count || 0 }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="内容数" width="120" align="center">
          <template #default="{ row }">
            <span>{{ row.content_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="发布渠道" width="200">
          <template #default="{ row }">
            <div class="channels">
              <el-tag
                v-for="channel in row.channels"
                :key="channel.channel"
                size="small"
                :type="channel.enabled ? 'success' : 'info'"
                style="margin-right: 4px"
              >
                {{ getChannelLabel(channel.channel) }} ({{ channel.publish_count || 0 }})
              </el-tag>
              <span v-if="!row.channels || row.channels.length === 0" class="hint">未配置</span>
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
            <el-button-group>
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
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, OfficeBuilding, Document, Avatar, Promotion, Search,
  View, Setting
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { getCommunities } from '../api/community'
import type { Community } from '../stores/auth'
import apiClient from '../api/index'

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
  // 切换到该社区并跳转到仪表板
  const community = communities.value.find(c => c.id === communityId)
  if (community) {
    // TODO: 实现社区详情页或切换社区
    ElMessage.info('社区详情页待实现')
  }
}

function viewCommittees(communityId: number) {
  // 切换社区并跳转到委员会列表
  router.push(`/committees?community=${communityId}`)
}

function manageCommunity(communityId: number) {
  router.push('/communities')
}

async function loadCommunities() {
  loading.value = true
  try {
    // 获取社区列表
    const communityList = await getCommunities()
    
    // 为每个社区获取统计信息
    const statsPromises = communityList.map(async (community) => {
      try {
        // 获取委员会数量
        const committeesRes = await apiClient.get(
          '/committees',
          {
            headers: { 'X-Community-Id': community.id }
          }
        )
        const committee_count = committeesRes.data?.length || 0

        // 获取内容数量
        const contentsRes = await apiClient.get(
          '/contents',
          {
            headers: { 'X-Community-Id': community.id }
          }
        )
        const content_count = contentsRes.data?.length || 0

        // 获取渠道信息
        const channelsRes = await apiClient.get(
          '/channels',
          {
            headers: { 'X-Community-Id': community.id }
          }
        )
        const channels = channelsRes.data || []

        // 为每个渠道获取发布数量
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
.community-overview {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.communities-card {
  margin-top: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.community-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.community-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.community-slug {
  font-size: 12px;
  color: #909399;
}

.channels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.hint {
  color: #c0c4cc;
  font-size: 12px;
}

.description {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
