<template>
  <div class="publish-view">
    <div class="page-header">
      <h2>发布管理 {{ content ? `- ${content.title}` : '' }}</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <div v-if="!contentId" class="select-hint">
      <el-empty description="请从内容列表选择要发布的文章" />
    </div>

    <template v-else>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>选择发布渠道</template>
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
          </el-card>

          <el-card style="margin-top: 16px" v-if="records.length">
            <template #header>发布记录</template>
            <div v-for="rec in records" :key="rec.id" class="record-item">
              <el-tag :type="rec.status === 'published' ? 'success' : rec.status === 'failed' ? 'danger' : 'warning'" size="small">
                {{ rec.status }}
              </el-tag>
              <span class="record-channel">{{ channelLabel(rec.channel) }}</span>
              <span class="record-time">{{ formatDate(rec.created_at) }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import copy from 'clipboard-copy'
import { fetchContent, type Content } from '../api/content'
import {
  getPreview, getCopyContent, publishToWechat, publishToHugo,
  getPublishRecords, type PublishRecord, type ChannelPreview,
} from '../api/publish'

const route = useRoute()
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
  if (contentId.value) {
    content.value = await fetchContent(contentId.value)
    records.value = await getPublishRecords(contentId.value)
  }
})

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
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.channel-list { display: flex; flex-direction: column; gap: 12px; }
.channel-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border: 1px solid #e4e7ed; border-radius: 8px; cursor: pointer; transition: all .2s;
}
.channel-item:hover { border-color: #409eff; }
.channel-item.active { border-color: #409eff; background: #ecf5ff; }
.channel-info { display: flex; align-items: center; gap: 12px; }
.channel-name { font-weight: 500; }
.channel-mode { font-size: 12px; color: #999; }
.record-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.record-channel { font-weight: 500; }
.record-time { color: #999; font-size: 13px; margin-left: auto; }
.preview-area { max-height: 600px; overflow-y: auto; }
.wechat-preview { padding: 16px; background: #fff; }
.markdown-preview { padding: 16px; background: #f8f8f8; border-radius: 4px; white-space: pre-wrap; font-size: 13px; line-height: 1.6; }
</style>
