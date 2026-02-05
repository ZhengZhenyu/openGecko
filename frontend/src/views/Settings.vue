<template>
  <div class="settings">
    <h2>渠道设置</h2>

    <el-row :gutter="20">
      <el-col :span="12" v-for="ch in channelList" :key="ch.key">
        <el-card style="margin-bottom: 20px">
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
                <el-input v-model="ch.config.app_secret" type="password" show-password placeholder="微信公众号 AppSecret" />
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
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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

onMounted(async () => {
  try {
    const configs = await getChannelConfigs()
    for (const cfg of configs) {
      const item = channelList.value.find(c => c.key === cfg.channel)
      if (item) {
        item.enabled = cfg.enabled
        item.config = { ...item.config, ...cfg.config }
      }
    }
  } catch { /* empty */ }
})

async function handleSave(ch: ChannelItem) {
  try {
    await updateChannelConfig(ch.key, { config: ch.config, enabled: ch.enabled })
    ElMessage.success(`${ch.label} 配置已保存`)
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
.settings h2 { margin: 0 0 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.hint-text { color: #999; font-size: 13px; }
</style>
