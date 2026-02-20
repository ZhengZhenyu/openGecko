<template>
  <div class="settings">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-title">
        <div>
          <h2>渠道设置</h2>
          <p class="subtitle">当前社区: <strong>{{ currentCommunityName }}</strong></p>
        </div>
      </div>

      <el-row :gutter="20">
        <el-col :span="12" v-for="ch in channelList" :key="ch.key">
          <div class="section-card" style="margin-bottom: 20px">
            <template #header>
              <div class="card-header">
                <span>{{ ch.label }}</span>
                <el-switch v-model="ch.enabled" @change="handleToggle(ch)" />
              </div>
            </template>

            <template v-if="ch.key === 'wechat'">
              <el-form label-width="100px" size="default">
                <el-form-item label="AppID">
                  <el-input v-model="ch.config.app_id" placeholder="微信公众号 AppID" />
                </el-form-item>
                <el-form-item label="AppSecret">
                  <el-input
                    v-model="ch.config.app_secret"
                    type="password"
                    show-password
                    placeholder="微信公众号 AppSecret"
                    @focus="handleSecretFocus(ch, 'app_secret')"
                  />
                  <div v-if="isSecretMasked(ch.config.app_secret)" class="secret-hint">已配置，留空则保持不变</div>
                </el-form-item>
              </el-form>
            </template>

            <template v-else-if="ch.key === 'hugo'">
              <el-form label-width="100px" size="default">
                <el-form-item label="仓库路径">
                  <el-input v-model="ch.config.repo_path" placeholder="Hugo 仓库本地路径" />
                </el-form-item>
                <el-form-item label="内容目录">
                  <el-input v-model="ch.config.content_dir" placeholder="如 content/posts" />
                </el-form-item>
              </el-form>
            </template>

            <template v-else-if="ch.key === 'csdn'">
              <el-form label-width="100px" size="default">
                <el-form-item label="说明">
                  <span class="hint-text">CSDN 使用复制粘贴方式发布，无需额外配置</span>
                </el-form-item>
              </el-form>
            </template>

            <template v-else-if="ch.key === 'zhihu'">
              <el-form label-width="100px" size="default">
                <el-form-item label="说明">
                  <span class="hint-text">知乎使用复制粘贴方式发布，无需额外配置</span>
                </el-form-item>
              </el-form>
            </template>

            <el-button v-if="['wechat', 'hugo'].includes(ch.key)" type="primary" size="small" @click="handleSave(ch)">
              保存配置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useCommunityStore } from '../stores/community'
import { useAuthStore } from '../stores/auth'
const communityStore = useCommunityStore()
const authStore = useAuthStore()

const currentCommunityId = computed(() => communityStore.currentCommunityId)
const currentCommunityName = computed(() => {
  const community = authStore.communities.find(c => c.id === currentCommunityId.value)
  return community?.name || '未选择'
})

import { getChannelConfigs, updateChannelConfig } from '../api/publish'

interface ChannelItem {
  key: string
  label: string
  enabled: boolean
  config: Record<string, string>
}

const channelList = ref<ChannelItem[]>([
  { key: 'wechat', label: '微信公众号', enabled: false, config: { app_id: '', app_secret: '' } },
  { key: 'hugo', label: 'Hugo 博客', enabled: false, config: { repo_path: '', content_dir: 'content/posts' } },
  { key: 'csdn', label: 'CSDN', enabled: false, config: {} },
  { key: 'zhihu', label: '知乎', enabled: false, config: {} },
])

/** Check if a value is a masked placeholder from backend */
function isSecretMasked(val: string): boolean {
  return !!val && val.startsWith('••••')
}

// Reload channels when community changes
watch(currentCommunityId, () => {
  loadChannels()
})

async function loadChannels() {
  if (!currentCommunityId.value) return
  
  // Reset to defaults
  channelList.value.forEach(ch => {
    ch.enabled = false
    ch.config = getDefaultConfig(ch.key)
  })
  
  try {
    const configs = await getChannelConfigs()
    for (const cfg of configs) {
      const item = channelList.value.find(c => c.key === cfg.channel)
      if (item) {
        item.enabled = cfg.enabled
        item.config = { ...item.config, ...cfg.config }
      }
    }
  } catch (error) {
    console.error('Failed to load channels:', error)
  }
}

async function handleSave(ch: ChannelItem) {
  // Build the config to send — skip masked values (means user didn't change them)
  const configToSend: Record<string, string> = {}
  for (const [k, v] of Object.entries(ch.config)) {
    if (!isSecretMasked(v)) {
      configToSend[k] = v
    }
    // If masked, simply don't include it — backend will keep existing value
  }

  try {
    await updateChannelConfig(ch.key, { config: configToSend, enabled: ch.enabled })
    ElMessage.success(`${ch.label} 配置已保存`)
    // Reload to get updated masked values
    const configs = await getChannelConfigs()
    for (const cfg of configs) {
      const item = channelList.value.find(c => c.key === cfg.channel)
      if (item) {
        item.enabled = cfg.enabled
        item.config = { ...item.config, ...cfg.config }
      }
    }
  } catch {
    ElMessage.error('保存失败')
  }
}

async function handleToggle(ch: ChannelItem) {
  try {
    await updateChannelConfig(ch.key, { enabled: ch.enabled })
  } catch {
    ch.enabled = !ch.enabled
  }
}
</script>

<style scoped>
.settings {
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

.page-title strong {
  color: var(--blue);
  font-weight: 600;
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.card-header span {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.hint-text {
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 6px;
  line-height: 1.5;
}

.secret-hint {
  color: var(--text-muted);
  font-size: 12px;
  margin-top: 6px;
  font-style: italic;
}

/* Element Plus form overrides */
:deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
}

:deep(.el-input__wrapper) {
  background: #ffffff;
  border: none;
  box-shadow: 0 0 0 1px #e2e8f0;
  transition: all 0.2s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd5e1;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #0095ff, 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
}

:deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

:deep(.el-switch) {
  --el-switch-on-color: #0095ff;
}

:deep(.el-empty) {
  color: var(--text-secondary);
}

:deep(.el-empty__description) {
  color: var(--text-muted);
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}

:deep(.el-button--primary:hover) {
  background: #007acc;
  border-color: #007acc;
}

:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  color: var(--text-primary);
}

:deep(.el-button--default:hover) {
  background: #f8fafc;
  border-color: #cbd5e1;
}
</style>
