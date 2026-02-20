<template>
  <div class="publish-view">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-title">
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
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="section-card">
              <div class="section-header">
                <h3>选择发布渠道</h3>
              </div>
              <div class="channel-list">
                <div
                  v-for="ch in channels"
                  :key="ch.key"
                  class="channel-item"
                  :class="{ active: activeChannel === ch.key }"
                  @click="selectChannel(ch.key)"
                >
                  <div class="channel-info">
                    <el-icon :size="20"><component :is="ch.icon" /></el-icon>
                    <div>
                      <div class="channel-name">{{ ch.name }}</div>
                      <div class="channel-mode">{{ ch.mode }}</div>
                    </div>
                  </div>
                  <el-button
                    v-if="ch.action === 'api'"
                    size="small"
                    type="primary"
                    :loading="publishing"
                    @click.stop="handlePublish(ch.key)"
                  >
                    发布
                  </el-button>
                  <el-button
                    v-else
                    size="small"
                    @click.stop="handleCopy(ch.key)"
                  >
                    复制内容
                  </el-button>
                </div>
              </div>
            </div>

            <el-card style="margin-top: 16px" v-if="records.length">
              <template #header>发布记录</template>
              <div v-for="rec in records" :key="rec.id" class="record-item">
                <el-tag :type="rec.status === 'published' ? 'success' : rec.status === 'failed' ? 'danger' : 'warning'" size="small">
                  {{ rec.status }}
                </el-tag>
              </div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                {{ activeChannel ? channelLabel(activeChannel) + ' 预览' : '渠道预览' }}
              </template>
              <div v-if="previewLoading" v-loading="true" style="min-height: 300px" />
              <div v-else-if="previewContent" class="preview-area">
                <div v-if="previewFormat === 'html'" v-html="previewContent" class="wechat-preview" />
                <pre v-else class="markdown-preview">{{ previewContent }}</pre>
              </div>
              <el-empty v-else description="点击左侧渠道查看预览" />
            </el-card>
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
  getPublishRecords, type PublishRecord, type ChannelPreview,
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
const publishing = ref(false)
const records = ref<PublishRecord[]>([])

const channels = [
  { key: 'wechat', name: '微信公众号', mode: 'API 创建草稿', icon: 'ChatDotRound', action: 'api' },
  { key: 'hugo', name: 'Hugo 博客', mode: '生成 Markdown 文件', icon: 'Document', action: 'api' },
  { key: 'csdn', name: 'CSDN', mode: '复制 Markdown', icon: 'Notebook', action: 'copy' },
  { key: 'zhihu', name: '知乎', mode: '复制富文本', icon: 'ChatLineSquare', action: 'copy' },
]

onMounted(async () => {
  if (communityStore.currentCommunityId && contentId.value) {
    content.value = await fetchContent(contentId.value)
    records.value = await getPublishRecords(contentId.value)
  }
})

// Watch for community changes
watch(
  () => communityStore.currentCommunityId,
  async (newId) => {
    if (newId && contentId.value) {
      content.value = await fetchContent(contentId.value)
      records.value = await getPublishRecords(contentId.value)
    }
  }
)

async function selectChannel(ch: string) {
  activeChannel.value = ch
  previewLoading.value = true
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

async function handlePublish(ch: string) {
  publishing.value = true
  try {
    if (ch === 'wechat') {
      await publishToWechat(contentId.value!)
      ElMessage.success('已创建微信草稿，请到公众号后台确认发布')
    } else if (ch === 'hugo') {
      await publishToHugo(contentId.value!)
      ElMessage.success('Hugo 文章已生成')
    }
    records.value = await getPublishRecords(contentId.value!)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

async function handleCopy(ch: string) {
  try {
    const data = await getCopyContent(contentId.value!, ch)
    await copy(data.content)
    ElMessage.success(`${channelLabel(ch)} 内容已复制到剪贴板`)
  } catch {
    ElMessage.error('复制失败')
  }
}

function channelLabel(ch: string) {
  const map: Record<string, string> = { wechat: '微信公众号', hugo: 'Hugo 博客', csdn: 'CSDN', zhihu: '知乎' }
  return map[ch] || ch
}

function formatDate(d: string) { return new Date(d).toLocaleString('zh-CN') }
</script>

<style scoped>
/* LFX Insights Light Theme - Publish View */
.publish-view {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
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

.channel-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.channel-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #ffffff;
}

.channel-item:hover {
  border-color: var(--blue);
  background: #eff6ff;
}

.channel-item.active {
  border-color: var(--blue);
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(0, 149, 255, 0.1);
}

.channel-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.channel-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.channel-mode {
  font-size: 13px;
  color: var(--text-muted);
}

.record-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.record-item:last-child {
  border-bottom: none;
}

.record-channel {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.record-time {
  color: var(--text-muted);
  font-size: 13px;
  margin-left: auto;
}

.preview-area {
  max-height: 600px;
  overflow-y: auto;
  border-radius: 12px;
}

.preview-area::-webkit-scrollbar {
  width: 8px;
}

.preview-area::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 4px;
}

.preview-area::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.preview-area::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

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
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  border: 1px solid var(--border);
}

.select-hint {
  padding: 60px 20px;
  text-align: center;
}

/* Element Plus dark theme overrides */
:deep(.el-empty) {
  color: var(--text-secondary);
}

:deep(.el-empty__description) {
  color: var(--text-muted);
}

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
</style>
