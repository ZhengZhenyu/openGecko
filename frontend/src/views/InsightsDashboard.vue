<template>
  <div class="insights-page">
    <!-- Header -->
    <div class="page-title-row">
      <div>
        <h2>洞察仪表板</h2>
        <p class="subtitle">生态趋势 · 关键人物 · 企业图谱</p>
      </div>
      <el-button :loading="refreshing" @click="refreshAll">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- ─── Section 1: 生态趋势 ─────────────────────────────────────── -->
    <div class="section-card" v-loading="trendsLoading">
      <div class="section-header">
        <h3>生态趋势</h3>
        <span class="section-hint">基于历史快照计算各项目近期动量</span>
      </div>

      <div v-if="!trendsLoading && trends.length === 0" class="empty-hint">
        暂无数据，请先添加项目并触发同步
      </div>

      <div class="trend-grid">
        <div
          v-for="t in trends"
          :key="t.project_id"
          class="trend-card"
          @click="selectProject(t.project_id, t.project_name)"
          :class="{ active: selectedProjectId === t.project_id }"
        >
          <div class="trend-card-top">
            <span class="project-name-text">{{ t.project_name }}</span>
            <span class="momentum-badge" :class="momentumClass(t.momentum)">
              {{ momentumLabel(t.momentum) }}
            </span>
          </div>

          <div class="velocity-bar-wrap">
            <div class="velocity-bar" :style="{ width: t.velocity_score + '%', background: velocityColor(t.momentum) }"></div>
          </div>
          <div class="velocity-label">综合增速 {{ t.velocity_score.toFixed(1) }}</div>

          <div class="trend-metrics">
            <div class="metric">
              <span class="metric-label">Stars +</span>
              <span class="metric-value">{{ t.star_growth_30d ?? '—' }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">贡献者 +</span>
              <span class="metric-value">{{ t.contributor_growth_30d ?? '—' }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">PR 合并</span>
              <span class="metric-value">{{ t.pr_merged_30d ?? '—' }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">活跃贡献者</span>
              <span class="metric-value">{{ t.active_contributors_30d ?? '—' }}</span>
            </div>
          </div>

          <div class="snapshot-info">
            快照 {{ t.snapshot_count }} 条
            <template v-if="t.latest_snapshot_at">
              · {{ formatDate(t.latest_snapshot_at) }}
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── Section 2: 关键人物 ─────────────────────────────────────── -->
    <div class="section-card" v-loading="influenceLoading">
      <div class="section-header">
        <h3>关键人物</h3>
        <el-select
          v-model="selectedProjectId"
          placeholder="全部项目"
          style="width: 220px"
          clearable
          @change="filterPersons"
        >
          <el-option
            v-for="t in trends"
            :key="t.project_id"
            :label="t.project_name"
            :value="t.project_id"
          />
        </el-select>
      </div>

      <div v-if="!influenceLoading && persons.length === 0" class="empty-hint">
        暂无贡献者数据
      </div>

      <el-table v-else :data="persons" style="width: 100%" :show-header="true">
        <el-table-column label="贡献者" min-width="180">
          <template #default="{ row }">
            <div class="person-cell">
              <img v-if="row.avatar_url" :src="row.avatar_url" class="avatar" />
              <div v-else class="avatar-placeholder">{{ (row.display_name || row.github_handle)[0].toUpperCase() }}</div>
              <div>
                <div class="person-name">{{ row.display_name || row.github_handle }}</div>
                <div class="person-handle">@{{ row.github_handle }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="影响力类型" min-width="220">
          <template #default="{ row }">
            <span
              v-for="t in row.influence_types"
              :key="t"
              class="influence-badge"
              :class="influenceBadgeClass(t)"
            >{{ influenceLabel(t) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="综合评分" width="110" align="center">
          <template #default="{ row }">
            <span class="score-chip">{{ row.influence_score.toFixed(1) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="Commits 90d" prop="commit_count_90d" width="120" align="center">
          <template #default="{ row }">{{ row.commit_count_90d ?? '—' }}</template>
        </el-table-column>

        <el-table-column label="跨项目" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.cross_project_count > 1" class="cross-badge">{{ row.cross_project_count }}</span>
            <span v-else class="muted-text">1</span>
          </template>
        </el-table-column>

        <el-table-column label="公司" min-width="140">
          <template #default="{ row }">
            <span v-if="row.company" class="company-text">{{ row.company }}</span>
            <span v-else class="muted-text">—</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ─── Section 3: 企业图谱 ─────────────────────────────────────── -->
    <div class="section-card" v-loading="corporateLoading">
      <div class="section-header">
        <h3>企业图谱</h3>
        <span class="section-hint">按跨项目战略贡献度排序</span>
      </div>

      <div v-if="!corporateLoading && corporates.length === 0" class="empty-hint">
        暂无企业数据，请确保贡献者已填写 company 字段
      </div>

      <el-table v-else :data="corporates" style="width: 100%">
        <el-table-column label="企业" min-width="180">
          <template #default="{ row }">
            <div class="company-row">
              <span class="company-name">{{ row.company }}</span>
              <span v-if="row.has_maintainer" class="maintainer-badge">Maintainer</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="战略评分" width="120" align="center">
          <template #default="{ row }">
            <div class="score-bar-wrap">
              <div class="score-bar" :style="{ width: row.strategic_score + '%' }"></div>
              <span class="score-bar-label">{{ row.strategic_score.toFixed(1) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="覆盖项目" width="100" align="center" prop="project_count" />
        <el-table-column label="贡献者数" width="100" align="center" prop="total_contributors" />

        <el-table-column label="项目分布" min-width="260">
          <template #default="{ row }">
            <div class="project-presence-list">
              <el-tooltip
                v-for="p in row.projects"
                :key="p.project_id"
                :content="`${p.project_name}：${p.contributor_count} 人，占比 ${(p.commit_share * 100).toFixed(1)}%`"
                placement="top"
              >
                <span class="presence-chip" :class="{ 'has-maintainer': p.has_maintainer }">
                  {{ p.project_name }}
                </span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import {
  getTrends, getPeople, getCorporate,
  type ProjectTrend, type KeyPerson, type CorporateLandscape, type MomentumLevel, type InfluenceType,
} from '../api/insights'

// ─── state ───────────────────────────────────────────────────────────────────

const trendsLoading = ref(false)
const influenceLoading = ref(false)
const corporateLoading = ref(false)
const refreshing = ref(false)

const trends = ref<ProjectTrend[]>([])
const allPersons = ref<KeyPerson[]>([])   // 全量，从 /insights/people 获取
const persons = ref<KeyPerson[]>([])       // 展示用（经 project 过滤）
const corporates = ref<CorporateLandscape[]>([])

const selectedProjectId = ref<number | null>(null)

// ─── helpers ─────────────────────────────────────────────────────────────────

function momentumLabel(m: MomentumLevel): string {
  return { accelerating: '加速增长', growing: '稳步增长', stable: '成熟稳定', declining: '活跃下降', insufficient_data: '数据不足' }[m] ?? m
}

function momentumClass(m: MomentumLevel): string {
  return { accelerating: 'mom-accel', growing: 'mom-grow', stable: 'mom-stable', declining: 'mom-decline', insufficient_data: 'mom-insuf' }[m] ?? ''
}

function velocityColor(m: MomentumLevel): string {
  return { accelerating: '#22c55e', growing: '#0095ff', stable: '#94a3b8', declining: '#ef4444', insufficient_data: '#e2e8f0' }[m] ?? '#e2e8f0'
}

function influenceLabel(t: InfluenceType): string {
  return { maintainer: 'Maintainer', bridge: '跨项目', rising_star: '新星', reviewer: 'Reviewer', contributor: '贡献者' }[t] ?? t
}

function influenceBadgeClass(t: InfluenceType): string {
  return { maintainer: 'inf-maintainer', bridge: 'inf-bridge', rising_star: 'inf-star', reviewer: 'inf-reviewer', contributor: 'inf-contributor' }[t] ?? ''
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// ─── data loading ────────────────────────────────────────────────────────────

async function loadTrends() {
  trendsLoading.value = true
  try {
    trends.value = await getTrends()
  } finally {
    trendsLoading.value = false
  }
}

async function loadPeople() {
  influenceLoading.value = true
  try {
    allPersons.value = await getPeople({ limit: 100 })
    filterPersons()
  } finally {
    influenceLoading.value = false
  }
}

/** 点击趋势卡片或切换下拉时，客户端过滤 persons */
function filterPersons() {
  if (!selectedProjectId.value) {
    persons.value = allPersons.value
  } else {
    persons.value = allPersons.value.filter(p => p.project_ids.includes(selectedProjectId.value!))
  }
}

function selectProject(id: number, _name: string) {
  selectedProjectId.value = id
  filterPersons()
}

async function loadCorporate() {
  corporateLoading.value = true
  try {
    corporates.value = await getCorporate()
  } finally {
    corporateLoading.value = false
  }
}

async function refreshAll() {
  refreshing.value = true
  try {
    await Promise.all([loadTrends(), loadPeople(), loadCorporate()])
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadTrends()
  loadPeople()
  loadCorporate()
})
</script>

<style scoped>
.insights-page {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --orange:         #f59e0b;
  --red:            #ef4444;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-hover:   0 4px 12px rgba(0,0,0,0.08);
  --radius:         12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ─── Header ─────────────────────────────────────── */
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

/* ─── Section card ───────────────────────────────── */
.section-card {
  background: #fff;
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
  margin-bottom: 20px;
}
.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.section-hint {
  font-size: 13px;
  color: var(--text-muted);
}
.empty-hint {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 14px;
}

/* ─── Trend grid ─────────────────────────────────── */
.trend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.trend-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.trend-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: var(--blue);
}
.trend-card.active {
  border-color: var(--blue);
  background: #f0f7ff;
}
.trend-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  gap: 8px;
}
.project-name-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

/* Momentum badges */
.momentum-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}
.mom-accel  { background: #f0fdf4; color: #15803d; }
.mom-grow   { background: #eff6ff; color: #1d4ed8; }
.mom-stable { background: #f1f5f9; color: #64748b; }
.mom-decline{ background: #fef2f2; color: #dc2626; }
.mom-insuf  { background: #f1f5f9; color: #94a3b8; }

/* Velocity bar */
.velocity-bar-wrap {
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}
.velocity-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}
.velocity-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

/* Metrics row */
.trend-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}
.metric {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.metric-label { color: var(--text-muted); }
.metric-value { font-weight: 600; color: var(--text-primary); }
.snapshot-info {
  margin-top: 10px;
  font-size: 11px;
  color: var(--text-muted);
}

/* ─── Influence table ────────────────────────────── */
.person-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.avatar-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #eff6ff;
  color: var(--blue);
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.person-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.person-handle { font-size: 11px; color: var(--text-muted); }

/* Influence type badges */
.influence-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 5px;
  margin-right: 4px;
  margin-bottom: 2px;
}
.inf-maintainer { background: #fffbeb; color: #b45309; }
.inf-bridge     { background: #eff6ff; color: #1d4ed8; }
.inf-star       { background: #f0fdf4; color: #15803d; }
.inf-reviewer   { background: #faf5ff; color: #7e22ce; }
.inf-contributor{ background: #f1f5f9; color: #64748b; }

.score-chip {
  display: inline-block;
  background: #eff6ff;
  color: var(--blue);
  font-size: 13px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 6px;
}
.cross-badge {
  display: inline-block;
  background: #eff6ff;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
  padding: 1px 8px;
  border-radius: 5px;
}
.company-text { font-size: 13px; color: var(--text-primary); }
.muted-text   { color: var(--text-muted); font-size: 13px; }

/* ─── Corporate table ────────────────────────────── */
.company-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.company-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.maintainer-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: #fffbeb;
  color: #b45309;
}

.score-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.score-bar {
  height: 6px;
  background: var(--blue);
  border-radius: 3px;
  min-width: 2px;
  max-width: 60px;
  flex-shrink: 0;
}
.score-bar-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.project-presence-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.presence-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 5px;
  background: #f1f5f9;
  color: var(--text-secondary);
}
.presence-chip.has-maintainer {
  background: #fffbeb;
  color: #b45309;
}

/* ─── Table overrides ────────────────────────────── */
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
  vertical-align: middle;
}
:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* ─── Responsive ─────────────────────────────────── */
@media (max-width: 1200px) {
  .insights-page { padding: 28px 24px; }
}
@media (max-width: 734px) {
  .insights-page { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
  .trend-grid { grid-template-columns: 1fr; }
}
</style>
