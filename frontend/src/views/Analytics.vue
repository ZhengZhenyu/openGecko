<template>
  <div class="analytics-view">
    <div class="page-title-row">
      <div>
        <h2>内容分析</h2>
        <p class="subtitle">当前社区多渠道内容发布概览与趋势</p>
      </div>
      <el-select v-model="trendDays" style="width: 120px" @change="loadTrend">
        <el-option :value="7"  label="最近 7 天" />
        <el-option :value="30" label="最近 30 天" />
        <el-option :value="90" label="最近 90 天" />
      </el-select>
    </div>

    <!-- 概览卡片 -->
    <div class="stats-grid" v-loading="overviewLoading">
      <div class="stat-card">
        <div class="stat-label">内容总数</div>
        <div class="stat-value">{{ overview?.total_contents ?? '—' }}</div>
        <div class="stat-sub">所有状态</div>
      </div>
      <div class="stat-card green">
        <div class="stat-label">累计发布次数</div>
        <div class="stat-value">{{ overview?.total_published ?? '—' }}</div>
        <div class="stat-sub">跨所有渠道</div>
      </div>
      <div
        v-for="(count, ch) in overview?.channels"
        :key="ch"
        class="stat-card blue"
      >
        <div class="stat-label">{{ channelLabel(ch) }}</div>
        <div class="stat-value">{{ count }}</div>
        <div class="stat-sub">已发布</div>
      </div>
    </div>

    <el-row :gutter="24" style="margin-top: 0">
      <!-- 渠道分布柱状图 -->
      <el-col :span="10">
        <div class="section-card">
          <div class="section-header"><h3>渠道发布分布</h3></div>
          <div v-if="!hasChannelData" class="chart-empty">
            <el-empty description="暂无发布数据" :image-size="80" />
          </div>
          <v-chart v-else class="chart" :option="barOption" autoresize />
        </div>
      </el-col>

      <!-- 发布趋势折线图 -->
      <el-col :span="14">
        <div class="section-card">
          <div class="section-header"><h3>发布趋势</h3></div>
          <div v-if="trendLoading" v-loading="true" style="height: 280px" />
          <div v-else-if="!hasTrendData" class="chart-empty">
            <el-empty description="暂无趋势数据" :image-size="80" />
          </div>
          <v-chart v-else class="chart" :option="lineOption" autoresize />
        </div>
      </el-col>
    </el-row>

    <!-- 渠道配置状态 -->
    <div class="section-card" style="margin-top: 0">
      <div class="section-header"><h3>渠道配置状态</h3></div>
      <div class="channel-status-grid">
        <div
          v-for="cfg in channelConfigs"
          :key="cfg.channel"
          class="channel-status-item"
          :class="{ enabled: cfg.enabled }"
        >
          <div class="channel-icon-wrap">
            <el-icon :size="22"><component :is="channelIcon(cfg.channel)" /></el-icon>
          </div>
          <span class="channel-name">{{ channelLabel(cfg.channel) }}</span>
          <span class="channel-badge" :class="cfg.enabled ? 'badge-green' : 'badge-gray'">
            {{ cfg.enabled ? '已启用' : '未配置' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useCommunityStore } from '../stores/community'
import {
  getAnalyticsOverview, getPublishTrend, getChannelConfigs,
  type AnalyticsOverview, type ChannelConfig,
} from '../api/publish'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const communityStore = useCommunityStore()
const overviewLoading = ref(false)
const trendLoading = ref(false)
const overview = ref<AnalyticsOverview | null>(null)
const trendItems = ref<{ date: string; count: number }[]>([])
const channelConfigs = ref<ChannelConfig[]>([])
const trendDays = ref(30)

async function loadOverview() {
  overviewLoading.value = true
  try {
    const [ov, cfgs] = await Promise.all([getAnalyticsOverview(), getChannelConfigs()])
    overview.value = ov
    channelConfigs.value = cfgs
  } catch { /* ignore */ } finally {
    overviewLoading.value = false
  }
}

async function loadTrend() {
  trendLoading.value = true
  try {
    const { items } = await getPublishTrend(trendDays.value)
    trendItems.value = items
  } catch { /* ignore */ } finally {
    trendLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadOverview(), loadTrend()])
})

watch(() => communityStore.currentCommunityId, () => {
  loadOverview()
  loadTrend()
})

const CHANNEL_NAMES: Record<string, string> = {
  wechat: '微信公众号', hugo: 'Hugo 博客', csdn: 'CSDN', zhihu: '知乎',
}
const CHANNEL_ICONS: Record<string, string> = {
  wechat: 'ChatDotRound', hugo: 'Document', csdn: 'Notebook', zhihu: 'ChatLineSquare',
}

function channelLabel(ch: string) { return CHANNEL_NAMES[ch] || ch }
function channelIcon(ch: string) { return CHANNEL_ICONS[ch] || 'Document' }

const hasChannelData = computed(() => {
  const ch = overview.value?.channels
  return ch && Object.keys(ch).length > 0 && Object.values(ch).some(v => (v as number) > 0)
})

const hasTrendData = computed(() => trendItems.value.some(i => i.count > 0))

const barOption = computed(() => {
  const ch = overview.value?.channels ?? {}
  const names = Object.keys(ch).map(channelLabel)
  const values = Object.values(ch) as number[]
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 12, left: 12, right: 12, bottom: 12, containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#64748b', fontSize: 12 },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [{
      type: 'bar',
      data: values,
      barMaxWidth: 56,
      itemStyle: {
        color: '#0095ff',
        borderRadius: [6, 6, 0, 0],
      },
    }],
  }
})

const lineOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
    formatter: (params: any[]) => {
      const p = params[0]
      return `${p.name}<br/>发布次数: <b>${p.value}</b>`
    },
  },
  grid: { top: 16, left: 12, right: 16, bottom: 12, containLabel: true },
  xAxis: {
    type: 'category',
    data: trendItems.value.map(i => i.date),
    axisLabel: {
      color: '#94a3b8', fontSize: 11,
      rotate: trendDays.value > 30 ? 45 : 0,
      interval: trendDays.value > 30 ? 6 : 'auto',
    },
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    boundaryGap: false,
  },
  yAxis: {
    type: 'value',
    minInterval: 1,
    axisLabel: { color: '#94a3b8', fontSize: 11 },
    splitLine: { lineStyle: { color: '#f1f5f9' } },
  },
  series: [{
    type: 'line',
    data: trendItems.value.map(i => i.count),
    smooth: true,
    symbol: 'circle',
    symbolSize: 5,
    lineStyle: { color: '#0095ff', width: 2 },
    itemStyle: { color: '#0095ff' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0,149,255,0.18)' },
          { offset: 1, color: 'rgba(0,149,255,0)' },
        ],
      },
    },
  }],
}))
</script>

<style scoped>
.analytics-view {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;

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

.page-title-row .subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

/* ── 概览卡片网格 ─────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 22px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-hover);
}

.stat-card.green { border-top: 3px solid #22c55e; }
.stat-card.blue  { border-top: 3px solid var(--blue); }

.stat-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 6px;
}

.stat-sub {
  font-size: 12px;
  color: var(--text-muted);
}

/* ── 区块卡片 ──────────────────────────────────── */
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}

.section-card:hover { box-shadow: var(--shadow-hover); }

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

/* ── 图表 ──────────────────────────────────────── */
.chart {
  height: 280px;
  width: 100%;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 280px;
}

/* ── 渠道配置状态 ──────────────────────────────── */
.channel-status-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.channel-status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #f8fafc;
  min-width: 180px;
}

.channel-status-item.enabled {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.channel-icon-wrap {
  color: var(--blue);
}

.channel-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.channel-badge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.badge-green {
  background: #f0fdf4;
  color: #15803d;
}

.badge-gray {
  background: #f1f5f9;
  color: #64748b;
}

/* Element Plus overrides */
:deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

@media (max-width: 1200px) {
  .analytics-view { padding: 28px 24px; }
  .stats-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
}

@media (max-width: 734px) {
  .analytics-view { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
}
</style>
