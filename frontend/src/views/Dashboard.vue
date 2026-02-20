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
      <div class="page-title">
        <h2>仪表板</h2>
        <p class="subtitle">社区内容与发布数据概览</p>
      </div>

      <!-- 指标卡片 -->
      <div class="metric-cards">
        <div class="metric-card">
          <div class="metric-value">{{ overview.total_contents }}</div>
          <div class="metric-label">内容总数</div>
        </div>
        <div class="metric-card highlight-success">
          <div class="metric-value">{{ overview.total_published }}</div>
          <div class="metric-label">已发布</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ Object.keys(overview.channels).length }}</div>
          <div class="metric-label">渠道覆盖</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ recentContents.length }}</div>
          <div class="metric-label">最近更新</div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="content-grid">
        <!-- 各渠道发布统计 -->
        <div class="section-card">
          <div class="section-header">
            <h3>各渠道发布统计</h3>
            <span class="section-desc">按发布渠道分类</span>
          </div>
          <div v-if="Object.keys(overview.channels).length === 0" class="empty-hint">
            <span>暂无发布记录</span>
          </div>
          <div v-else>
            <div v-for="(count, channel) in overview.channels" :key="channel" class="list-item">
              <div class="channel-info">
                <span class="channel-dot" :class="channelDotClass(channel as string)"></span>
                <span class="item-title">{{ channelLabel(channel as string) }}</span>
              </div>
              <span class="count-badge content-badge">{{ count }} 篇</span>
            </div>
          </div>
        </div>

        <!-- 最近内容 -->
        <div class="section-card">
          <div class="section-header">
            <h3>最近内容</h3>
            <span class="section-desc">最新 5 条内容</span>
          </div>
          <div v-if="recentContents.length === 0" class="empty-hint">
            <span>暂无内容</span>
          </div>
          <div v-else>
            <div v-for="item in recentContents" :key="item.id" class="list-item">
              <router-link :to="`/contents/${item.id}/edit`" class="item-title link">{{ item.title }}</router-link>
              <span class="status-tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
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
  if (!authStore.user) {
    try {
      const userInfo = await getUserInfo()
      authStore.setUser(userInfo.user)
      authStore.setCommunities(userInfo.communities)
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    }
  }

  if (communityStore.currentCommunityId) {
    await loadDashboardData()
  }
})

watch(
  () => communityStore.currentCommunityId,
  async (newId) => {
    if (newId) {
      await loadDashboardData()
    }
  }
)

async function loadDashboardData() {
  try {
    overview.value = await getAnalyticsOverview()
  } catch { /* empty */ }
  try {
    const res = await fetchContents({ page: 1, page_size: 5 })
    recentContents.value = res.items
  } catch { /* empty */ }
}

function channelLabel(ch: string) {
  const map: Record<string, string> = { wechat: '微信公众号', hugo: 'Hugo 博客', csdn: 'CSDN', zhihu: '知乎' }
  return map[ch] || ch
}

function channelDotClass(ch: string) {
  const map: Record<string, string> = { wechat: 'dot-success', hugo: 'dot-primary', csdn: 'dot-warning', zhihu: 'dot-info' }
  return map[ch] || 'dot-primary'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布' }
  return map[s] || s
}

function statusClass(s: string) {
  const map: Record<string, string> = { draft: 'status-planning', reviewing: 'status-in-progress', approved: 'status-completed', published: 'status-primary' }
  return map[s] || 'status-planning'
}
</script>

<style scoped>
/* LFX Insights Light Theme */
.dashboard {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --dark-blue: #00347b;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --bg-page: #f5f7fa;
  --bg-card: #ffffff;
  --border: #e2e8f0;
  --border-hover: #cbd5e1;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Page Title */
.page-title {
  margin-bottom: 32px;
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

/* Metric Cards */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.metric-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: var(--border-hover);
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
  margin-bottom: 6px;
}

.metric-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.metric-card.highlight-success .metric-value {
  color: var(--green);
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

/* Section Card */
.section-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
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
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-desc {
  font-size: 13px;
  color: var(--text-muted);
}

/* List Item */
.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.15s ease;
}

.list-item:last-child {
  border-bottom: none;
}

.list-item:hover {
  padding-left: 4px;
}

.channel-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.channel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.channel-dot.dot-success { background: var(--green); }
.channel-dot.dot-primary { background: var(--blue); }
.channel-dot.dot-warning { background: var(--orange); }
.channel-dot.dot-info { background: var(--text-muted); }

.item-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.item-title.link {
  text-decoration: none;
  cursor: pointer;
  transition: color 0.15s ease;
}

.item-title.link:hover {
  color: var(--blue);
}

/* Count Badge */
.count-badge {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
}

.content-badge {
  background: #eff6ff;
  color: var(--blue);
}

/* Status Tag */
.status-tag {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
}

.status-planning {
  background: #f1f5f9;
  color: var(--text-secondary);
}

.status-in-progress {
  background: #fffbeb;
  color: #b45309;
}

.status-completed {
  background: #f0fdf4;
  color: #15803d;
}

.status-primary {
  background: #eff6ff;
  color: #1d4ed8;
}

/* Empty States */
.empty-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  text-align: center;
  padding: 48px 24px;
  font-size: 14px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.empty-tip {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 12px 0 20px;
}

/* Responsive */
@media (max-width: 1068px) {
  .metric-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 734px) {
  .dashboard {
    padding: 24px 20px 48px;
  }

  .page-title h2 {
    font-size: 22px;
  }

  .metric-cards {
    gap: 12px;
  }

  .metric-value {
    font-size: 28px;
  }

  .content-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .section-header h3 {
    font-size: 16px;
  }
}
</style>
