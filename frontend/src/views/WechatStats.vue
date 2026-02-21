<template>
  <div class="wechat-stats">
    <div v-if="!communityStore.currentCommunityId" class="empty-state">
      <el-empty description="请先选择一个社区" :image-size="150">
        <p class="empty-tip">使用顶部的社区切换器选择要管理的社区</p>
      </el-empty>
    </div>

    <template v-else>
      <!-- Page Header -->
      <div class="page-title">
        <div>
          <h2>微信阅读统计</h2>
          <p class="subtitle">文章阅读量 · 互动数据 · 粉丝增长趋势分析</p>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="skeleton-wrap">
        <el-skeleton :rows="4" animated />
      </div>

      <template v-else>
        <!-- Overview Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ overview?.total_wechat_articles ?? 0 }}</div>
              <div class="stat-label">微信文章总数</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon green">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(overview?.total_read_count ?? 0) }}</div>
              <div class="stat-label">累计阅读量</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon orange">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(overview?.total_interaction_count ?? 0) }}</div>
              <div class="stat-label">互动总量</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon purple">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ overview?.category_summary?.length ?? 0 }}</div>
              <div class="stat-label">活跃分类</div>
            </div>
          </div>
        </div>

        <!-- Trend Chart + Filter -->
        <div class="section-card">
          <div class="section-header">
            <h3>阅读趋势</h3>
            <div class="filter-group">
              <el-select v-model="trendPeriod" size="small" style="width: 120px" @change="loadTrend">
                <el-option label="按天" value="daily" />
                <el-option label="按周" value="weekly" />
                <el-option label="按月" value="monthly" />
                <el-option label="按季度" value="quarterly" />
              </el-select>
              <el-select
                v-model="trendCategory"
                size="small"
                style="width: 130px"
                clearable
                placeholder="全部分类"
                @change="loadTrend"
              >
                <el-option label="版本发布" value="release" />
                <el-option label="技术文章" value="technical" />
                <el-option label="活动" value="activity" />
              </el-select>
            </div>
          </div>
          <div v-if="trendData && trendData.data_points.length > 0">
            <v-chart class="chart" :option="trendChartOption" autoresize />
          </div>
          <el-empty v-else description="暂无趋势数据" :image-size="80" />
        </div>

        <!-- Category Summary -->
        <div v-if="overview && overview.category_summary.length > 0" class="section-card">
          <div class="section-header">
            <h3>分类统计</h3>
          </div>
          <el-table :data="overview.category_summary" class="lfx-table">
            <el-table-column label="分类" prop="category_label" width="120" />
            <el-table-column label="文章数" prop="article_count" width="100" align="right" />
            <el-table-column label="总阅读量" prop="total_read_count" align="right">
              <template #default="{ row }">{{ formatNumber(row.total_read_count) }}</template>
            </el-table-column>
            <el-table-column label="均阅读量" prop="avg_read_count" align="right">
              <template #default="{ row }">{{ formatNumber(row.avg_read_count) }}</template>
            </el-table-column>
            <el-table-column label="点赞" prop="total_like_count" align="right" />
            <el-table-column label="分享" prop="total_share_count" align="right" />
            <el-table-column label="评论" prop="total_comment_count" align="right" />
          </el-table>
        </div>

        <!-- Article Ranking -->
        <div class="section-card">
          <div class="section-header">
            <h3>文章阅读排名</h3>
            <div class="filter-group">
              <el-select
                v-model="rankingCategory"
                size="small"
                style="width: 130px"
                clearable
                placeholder="全部分类"
                @change="loadRanking"
              >
                <el-option label="版本发布" value="release" />
                <el-option label="技术文章" value="technical" />
                <el-option label="活动" value="activity" />
              </el-select>
            </div>
          </div>
          <el-table :data="ranking" class="lfx-table">
            <el-table-column label="排名" type="index" width="70" align="center" />
            <el-table-column label="文章标题" prop="title" min-width="200" show-overflow-tooltip />
            <el-table-column label="分类" width="110">
              <template #default="{ row }">
                <span :class="['category-tag', row.article_category]">
                  {{ CATEGORY_LABELS[row.article_category] ?? row.article_category }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="阅读量" prop="read_count" width="100" align="right">
              <template #default="{ row }">{{ formatNumber(row.read_count) }}</template>
            </el-table-column>
            <el-table-column label="点赞" prop="like_count" width="80" align="right" />
            <el-table-column label="分享" prop="share_count" width="80" align="right" />
            <el-table-column label="评论" prop="comment_count" width="80" align="right" />
            <el-table-column label="发布时间" width="160">
              <template #default="{ row }">
                {{ row.published_at ? formatDate(row.published_at) : '—' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!ranking.length" description="暂无文章统计数据" :image-size="80" />
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useCommunityStore } from '../stores/community'
import {
  getWechatStatsOverview,
  getWechatStatsTrend,
  getWechatArticleRanking,
  type WechatStatsOverview,
  type TrendResponse,
  type ArticleRankItem,
} from '../api/wechatStats'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent])

const communityStore = useCommunityStore()

const loading = ref(false)
const overview = ref<WechatStatsOverview | null>(null)
const trendData = ref<TrendResponse | null>(null)
const ranking = ref<ArticleRankItem[]>([])

const trendPeriod = ref('daily')
const trendCategory = ref<string>('')
const rankingCategory = ref<string>('')

const CATEGORY_LABELS: Record<string, string> = {
  release: '版本发布',
  technical: '技术文章',
  activity: '活动',
}

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toString()
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// ── ECharts option ──

const trendChartOption = computed(() => {
  const points = trendData.value?.data_points ?? []
  const dates = points.map((p) => p.date)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['阅读量', '点赞', '分享'],
      bottom: 0,
      textStyle: { color: '#64748b', fontSize: 12 },
    },
    grid: { top: 16, left: 16, right: 16, bottom: 48, containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [
      {
        name: '阅读量',
        type: 'line',
        smooth: true,
        data: points.map((p) => p.read_count),
        itemStyle: { color: '#0095ff' },
        lineStyle: { color: '#0095ff', width: 2 },
        areaStyle: { color: 'rgba(0, 149, 255, 0.06)' },
      },
      {
        name: '点赞',
        type: 'line',
        smooth: true,
        data: points.map((p) => p.like_count),
        itemStyle: { color: '#22c55e' },
        lineStyle: { color: '#22c55e', width: 2 },
      },
      {
        name: '分享',
        type: 'line',
        smooth: true,
        data: points.map((p) => p.share_count),
        itemStyle: { color: '#f59e0b' },
        lineStyle: { color: '#f59e0b', width: 2 },
      },
    ],
  }
})

// ── Data Loading ──

async function loadAll() {
  if (!communityStore.currentCommunityId) return
  loading.value = true
  try {
    const [ov, rank] = await Promise.all([
      getWechatStatsOverview(),
      getWechatArticleRanking({ limit: 50 }),
    ])
    overview.value = ov
    ranking.value = rank
    await loadTrend()
  } catch (e) {
    console.error('Failed to load wechat stats', e)
  } finally {
    loading.value = false
  }
}

async function loadTrend() {
  if (!communityStore.currentCommunityId) return
  try {
    trendData.value = await getWechatStatsTrend({
      period_type: trendPeriod.value,
      category: trendCategory.value || undefined,
    })
  } catch (e) {
    console.error('Failed to load trend data', e)
  }
}

async function loadRanking() {
  try {
    ranking.value = await getWechatArticleRanking({
      category: rankingCategory.value || undefined,
      limit: 50,
    })
  } catch (e) {
    console.error('Failed to load ranking', e)
  }
}

onMounted(() => {
  if (communityStore.currentCommunityId) loadAll()
})

watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) loadAll()
    else {
      overview.value = null
      trendData.value = null
      ranking.value = []
    }
  }
)
</script>

<style scoped>
.wechat-stats {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --orange: #f59e0b;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-tip {
  color: var(--text-secondary);
  font-size: 13px;
  margin: 8px 0 0;
}

/* ── Page title ── */
.page-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 28px;
}

.page-title h2 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Stat cards ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-icon.blue {
  background: #eff6ff;
  color: #1d4ed8;
}

.stat-icon.green {
  background: #f0fdf4;
  color: #15803d;
}

.stat-icon.orange {
  background: #fffbeb;
  color: #b45309;
}

.stat-icon.purple {
  background: #f5f3ff;
  color: #6d28d9;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* ── Section cards ── */
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.filter-group {
  display: flex;
  gap: 8px;
}

/* ── Chart ── */
.chart {
  height: 280px;
}

/* ── Table ── */
.lfx-table {
  width: 100%;
}

:deep(.el-table th) {
  background: #f8fafc;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border);
}

:deep(.el-table tr:hover > td) {
  background: #f8fafc;
}

:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
  color: var(--text-primary);
  font-size: 14px;
}

/* ── Category tags ── */
.category-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.category-tag.release {
  background: #eff6ff;
  color: #1d4ed8;
}

.category-tag.technical {
  background: #f0fdf4;
  color: #15803d;
}

.category-tag.activity {
  background: #fffbeb;
  color: #b45309;
}

/* ── Skeleton ── */
.skeleton-wrap {
  padding: 24px;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .wechat-stats {
    padding: 24px 20px 40px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
