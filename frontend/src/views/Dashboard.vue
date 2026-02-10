<template>
  <div class="dashboard">
    <!-- No communities: empty state -->
    <div v-if="authStore.communities.length === 0" class="empty-state">
      <el-empty description="您还没有加入任何社区" :image-size="200">
        <template v-if="authStore.isSuperuser">
          <p class="empty-tip">作为超级管理员，您可以创建社区开始使用</p>
          <el-button type="primary" @click="$router.push('/communities')">创建社区</el-button>
        </template>
        <template v-else>
          <p class="empty-tip">请联系管理员将您添加到社区</p>
        </template>
      </el-empty>
    </div>

    <!-- Has communities but none selected -->
    <div v-else-if="!communityStore.currentCommunityId" class="empty-state">
      <el-empty description="请先选择一个社区" :image-size="150">
        <p class="empty-tip">使用顶部的社区切换器选择要管理的社区</p>
      </el-empty>
    </div>

    <!-- Normal dashboard -->
    <div v-else>
      <h2>仪表板</h2>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>内容总数</template>
            <div class="stat-number">{{ overview.total_contents }}</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>已发布</template>
            <div class="stat-number">{{ overview.total_published }}</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>渠道覆盖</template>
            <div class="stat-number">{{ Object.keys(overview.channels).length }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>各渠道发布统计</template>
            <div v-if="Object.keys(overview.channels).length === 0" class="empty-hint">暂无发布记录</div>
            <div v-else>
              <div v-for="(count, channel) in overview.channels" :key="channel" class="channel-stat">
                <el-tag :type="channelTagType(channel as string)">{{ channelLabel(channel as string) }}</el-tag>
                <span class="channel-count">{{ count }} 篇</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>最近内容</template>
            <div v-if="recentContents.length === 0" class="empty-hint">暂无内容</div>
            <div v-for="item in recentContents" :key="item.id" class="recent-item">
              <router-link :to="`/contents/${item.id}/edit`" class="recent-title">{{ item.title }}</router-link>
              <el-tag size="small" :type="statusType(item.status)">{{ statusLabel(item.status) }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchContents, type ContentListItem } from '../api/content'
import { getAnalyticsOverview, type AnalyticsOverview } from '../api/publish'
import { getUserInfo } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'

const authStore = useAuthStore()
const communityStore = useCommunityStore()

const overview = ref<AnalyticsOverview>({ total_contents: 0, total_published: 0, channels: {} })
const recentContents = ref<ContentListItem[]>([])

onMounted(async () => {
  // Fetch user info if not already loaded
  if (!authStore.user) {
    try {
      const userInfo = await getUserInfo()
      authStore.setUser(userInfo.user)
      authStore.setCommunities(userInfo.communities)
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    }
  }

  // Only load data when a community is selected
  if (!communityStore.currentCommunityId) return

  try {
    overview.value = await getAnalyticsOverview()
  } catch { /* empty */ }
  try {
    const res = await fetchContents({ page: 1, page_size: 5 })
    recentContents.value = res.items
  } catch { /* empty */ }
})

function channelLabel(ch: string) {
  const map: Record<string, string> = { wechat: '微信公众号', hugo: 'Hugo 博客', csdn: 'CSDN', zhihu: '知乎' }
  return map[ch] || ch
}

function channelTagType(ch: string) {
  const map: Record<string, string> = { wechat: 'success', hugo: '', csdn: 'warning', zhihu: 'info' }
  return (map[ch] || '') as any
}

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布' }
  return map[s] || s
}

function statusType(s: string) {
  const map: Record<string, string> = { draft: 'info', reviewing: 'warning', approved: 'success', published: '' }
  return (map[s] || 'info') as any
}
</script>

<style scoped>
.dashboard h2 { margin: 0 0 20px; }
.stat-number { font-size: 36px; font-weight: bold; color: #409eff; text-align: center; padding: 10px 0; }
.channel-stat { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.channel-count { font-size: 16px; font-weight: 500; }
.recent-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.recent-title { color: #333; text-decoration: none; }
.recent-title:hover { color: #409eff; }
.empty-hint { color: #999; text-align: center; padding: 20px 0; }
.empty-state { display: flex; justify-content: center; align-items: center; min-height: 400px; }
.empty-tip { color: #909399; font-size: 14px; margin: 8px 0 16px; }
</style>
