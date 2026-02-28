<template>
  <div class="publish-view">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #94a3b8; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-title-row">
        <div>
          <h2>发布管理</h2>
          <p class="subtitle">{{ content ? content.title : '多渠道发布内容' }}</p>
        </div>
        <el-button @click="$router.back()">返回</el-button>
      </div>

      <div v-if="!contentId" class="select-hint">
        <el-empty description="请从内容列表选择要发布的文章" />
      </div>

      <template v-else>
        <el-row :gutter="24">
          <!-- 左栏：渠道选择 -->
          <el-col :span="12">
            <div class="section-card">
              <div class="section-header">
                <h3>选择发布渠道</h3>
                <el-button
                  type="primary"
                  :disabled="checkedChannels.length === 0"
                  :loading="batchPublishing"
                  @click="handleBatchPublish"
                >
                  发布选中渠道 ({{ checkedChannels.length }})
                </el-button>
              </div>

              <div class="channel-list">
                <div
                  v-for="ch in channels"
                  :key="ch.key"
                  class="channel-item"
                  :class="{
                    active: activeChannel === ch.key,
                    disabled: !ch.configured,
                    'result-ok': publishResults[ch.key] === 'ok',
                    'result-err': publishResults[ch.key] === 'error',
                    'result-copied': publishResults[ch.key] === 'copied',
                  }"
                  @click="selectChannel(ch.key)"
                >
                  <!-- 左侧：复选框 + 图标 + 名称 -->
                  <div class="channel-left">
                    <el-checkbox
                      :model-value="checkedChannels.includes(ch.key)"
                      :disabled="!ch.configured"
                      @change="(val: boolean) => toggleChannel(ch.key, val)"
                      @click.stop
                    />
                    <el-icon :size="20" :style="{ color: ch.configured ? 'var(--blue)' : 'var(--text-muted)' }">
                      <component :is="ch.icon" />
                    </el-icon>
                    <div>
                      <div class="channel-name">{{ ch.name }}</div>
                      <div class="channel-mode">
                        <span v-if="!ch.configured" style="color: #ef4444">未配置渠道凭证</span>
                        <span v-else>{{ ch.mode }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 右侧：结果标签 -->
                  <div class="channel-right">
                    <el-tag v-if="publishResults[ch.key] === 'ok'" type="success" size="small">已发布</el-tag>
                    <el-tag v-else-if="publishResults[ch.key] === 'copied'" type="info" size="small">已复制</el-tag>
                    <el-tag v-else-if="publishResults[ch.key] === 'error'" type="danger" size="small">失败</el-tag>
                    <span v-else-if="ch.action === 'copy'" class="mode-badge copy">复制</span>
                    <span v-else class="mode-badge api">API</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 发布记录 -->
            <div class="section-card" v-if="records.length">
              <div class="section-header">
                <h3>发布记录</h3>
              </div>
              <div v-for="rec in records" :key="rec.id" class="record-item">
                <el-tag
                  :type="rec.status === 'published' ? 'success' : rec.status === 'failed' ? 'danger' : 'warning'"
                  size="small"
                >{{ rec.status }}</el-tag>
                <span class="record-channel">{{ channelLabel(rec.channel) }}</span>
                <span class="record-time">{{ rec.published_at ? formatDate(rec.published_at) : '—' }}</span>
              </div>
            </div>
          </el-col>

          <!-- 右栏：预览 -->
          <el-col :span="12">
            <div class="section-card preview-card">
              <div class="section-header">
                <h3>{{ activeChannel ? channelLabel(activeChannel) + ' 预览' : '渠道预览' }}</h3>
              </div>
              <div v-if="previewLoading" v-loading="true" style="min-height: 300px" />
              <div v-else-if="previewContent" class="preview-area">
                <div v-if="previewFormat === 'html'" v-html="previewContent" class="wechat-preview" />
                <pre v-else class="markdown-preview">{{ previewContent }}</pre>
              </div>
              <el-empty v-else description="点击左侧渠道查看预览" :image-size="80" />
            </div>
          </el-col>
        </el-row>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import copy from 'clipboard-copy'
import { fetchContent, type Content } from '../api/content'
import {
  getPreview, getCopyContent, publishToWechat, publishToHugo,
  getPublishRecords, getChannelConfigs, type PublishRecord, type ChannelPreview,
} from '../api/publish'
import { useCommunityStore } from '../stores/community'

const route = useRoute()
const communityStore = useCommunityStore()
const contentId = computed(() => route.params.id ? Number(route.params.id) : null)
const content = ref<Content | null>(null)
const activeChannel = ref('')
const previewContent = ref('')
const previewFormat = ref('html')
const previewLoading = ref(false)
const batchPublishing = ref(false)
const records = ref<PublishRecord[]>([])

// 渠道复选框状态（选中的 key 列表）
const checkedChannels = ref<string[]>([])
// 批量发布结果：key → 'ok' | 'error' | 'copied'
const publishResults = ref<Record<string, string>>({})
// 各渠道是否已配置
const configuredSet = ref<Set<string>>(new Set())

interface ChannelDef {
  key: string
  name: string
  mode: string
  icon: string
  action: 'api' | 'copy'
  configured: boolean
}

const channelDefs: Omit<ChannelDef, 'configured'>[] = [
  { key: 'wechat', name: '微信公众号', mode: 'API 创建草稿', icon: 'ChatDotRound', action: 'api' },
  { key: 'hugo',  name: 'Hugo 博客',   mode: '生成 Markdown 文件', icon: 'Document', action: 'api' },
  { key: 'csdn',  name: 'CSDN',        mode: '复制 Markdown',   icon: 'Notebook', action: 'copy' },
  { key: 'zhihu', name: '知乎',         mode: '复制富文本',       icon: 'ChatLineSquare', action: 'copy' },
]

const channels = computed<ChannelDef[]>(() =>
  channelDefs.map(ch => ({ ...ch, configured: configuredSet.value.has(ch.key) }))
)

async function loadData() {
  if (!communityStore.currentCommunityId || !contentId.value) return
  const [c, r, cfgs] = await Promise.all([
    fetchContent(contentId.value),
    getPublishRecords(contentId.value),
    getChannelConfigs().catch(() => []),
  ])
  content.value = c
  records.value = r
  // 标记已配置且启用的渠道
  configuredSet.value = new Set(
    cfgs.filter((cfg: any) => cfg.enabled).map((cfg: any) => cfg.channel as string)
  )
  // 默认勾选所有已配置渠道
  checkedChannels.value = [...configuredSet.value]
}

onMounted(loadData)
watch(() => communityStore.currentCommunityId, loadData)

function toggleChannel(key: string, val: boolean) {
  if (val) {
    if (!checkedChannels.value.includes(key)) checkedChannels.value.push(key)
  } else {
    checkedChannels.value = checkedChannels.value.filter(k => k !== key)
  }
}

async function selectChannel(ch: string) {
  if (activeChannel.value === ch) return
  activeChannel.value = ch
  previewLoading.value = true
  previewContent.value = ''
  try {
    const data: ChannelPreview = await getPreview(contentId.value!, ch)
    previewContent.value = data.content
    previewFormat.value = data.format
  } catch {
    previewContent.value = ''
  } finally {
    previewLoading.value = false
  }
}

async function handleBatchPublish() {
  if (!contentId.value || checkedChannels.value.length === 0) return
  batchPublishing.value = true
  publishResults.value = {}
  const tasks = checkedChannels.value.map(async (ch) => {
    const def = channelDefs.find(d => d.key === ch)
    if (!def) return
    try {
      if (def.action === 'api') {
        if (ch === 'wechat') await publishToWechat(contentId.value!)
        else if (ch === 'hugo') await publishToHugo(contentId.value!)
        publishResults.value[ch] = 'ok'
      } else {
        const data = await getCopyContent(contentId.value!, ch)
        await copy(data.content)
        publishResults.value[ch] = 'copied'
      }
    } catch {
      publishResults.value[ch] = 'error'
    }
  })
  await Promise.allSettled(tasks)
  batchPublishing.value = false

  const ok    = Object.values(publishResults.value).filter(v => v === 'ok').length
  const copied = Object.values(publishResults.value).filter(v => v === 'copied').length
  const err   = Object.values(publishResults.value).filter(v => v === 'error').length
  const parts: string[] = []
  if (ok)     parts.push(`${ok} 个渠道发布成功`)
  if (copied) parts.push(`${copied} 个渠道内容已复制到剪贴板`)
  if (err)    parts.push(`${err} 个渠道失败`)
  if (err > 0) ElMessage.warning(parts.join('，'))
  else         ElMessage.success(parts.join('，'))

  records.value = await getPublishRecords(contentId.value!)
}

function channelLabel(ch: string) {
  const map: Record<string, string> = { wechat: '微信公众号', hugo: 'Hugo 博客', csdn: 'CSDN', zhihu: '知乎' }
  return map[ch] || ch
}

function formatDate(d: string) { return new Date(d).toLocaleString('zh-CN') }
</script>

<style scoped>
.publish-view {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --red:            #ef4444;
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
  color: var(--text-secondary);
  font-size: 15px;
}

.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}

.section-card:hover {
  box-shadow: var(--shadow-hover);
}

.preview-card {
  min-height: 480px;
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

/* ── 渠道列表 ─────────────────────────────────── */
.channel-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.channel-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  background: #ffffff;
  user-select: none;
}

.channel-item:hover:not(.disabled) {
  border-color: var(--blue);
  background: #f0f9ff;
}

.channel-item.active {
  border-color: var(--blue);
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(0, 149, 255, 0.1);
}

.channel-item.disabled {
  opacity: 0.55;
  cursor: default;
}

.channel-item.result-ok {
  border-color: #86efac;
  background: #f0fdf4;
}

.channel-item.result-copied {
  border-color: #93c5fd;
  background: #eff6ff;
}

.channel-item.result-err {
  border-color: #fca5a5;
  background: #fef2f2;
}

.channel-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.channel-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.channel-mode {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

.mode-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.mode-badge.api {
  background: #eff6ff;
  color: #1d4ed8;
}

.mode-badge.copy {
  background: #f1f5f9;
  color: #64748b;
}

/* ── 发布记录 ─────────────────────────────────── */
.record-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}

.record-item:last-child {
  border-bottom: none;
}

.record-channel {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
}

.record-time {
  font-size: 13px;
  color: var(--text-muted);
  margin-left: auto;
}

/* ── 预览区域 ─────────────────────────────────── */
.preview-area {
  max-height: 600px;
  overflow-y: auto;
  border-radius: 10px;
}

.preview-area::-webkit-scrollbar { width: 6px; }
.preview-area::-webkit-scrollbar-track { background: #f8fafc; border-radius: 3px; }
.preview-area::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.preview-area::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.wechat-preview {
  padding: 20px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid var(--border);
}

.markdown-preview {
  padding: 20px;
  background: #f8fafc;
  border-radius: 10px;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  border: 1px solid var(--border);
}

.select-hint {
  padding: 60px 20px;
  text-align: center;
}

/* ── Element Plus overrides ───────────────────── */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

:deep(.el-button--default:hover) {
  background: #f8fafc;
  border-color: #cbd5e1;
}

:deep(.el-checkbox__inner) {
  border-radius: 4px;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--blue);
  border-color: var(--blue);
}

@media (max-width: 1200px) {
  .publish-view { padding: 28px 24px; }
}

@media (max-width: 734px) {
  .publish-view { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
}
</style>
