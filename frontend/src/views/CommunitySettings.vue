<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, WarningFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useCommunityStore } from '@/stores/community'
import {
  getCommunity, updateCommunityBasic, deleteCommunity,
  getCommunityUsers, addUserToCommunity, removeUserFromCommunity, updateUserRole,
  getEmailSettings, updateEmailSettings, testEmailSettings,
} from '@/api/community'
import { listChannels, createChannel, updateChannel, deleteChannel } from '@/api/channel'
import { listAllUsers } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const communityId = computed(() =>
  Number(route.params.communityId) || communityStore.currentCommunityId || 0
)

const canEditBasic = computed(() =>
  authStore.isSuperuser || authStore.isAdminInCommunity(communityId.value)
)

// ─── community data ────────────────────────────────────────────────────────────
const community = ref<any>(null)
const activeTab = ref('basic')

// ─── Tab 1: basic ──────────────────────────────────────────────────────────────
const basicFormRef = ref()
const basicForm = ref({ name: '', description: '', url: '', logo_url: '' })
const basicRules = {
  name: [{ required: true, message: '请填写社区名称', trigger: 'blur' }],
}
const savingBasic = ref(false)

async function saveBasicInfo() {
  const valid = await basicFormRef.value?.validate().catch(() => false)
  if (!valid) return
  savingBasic.value = true
  try {
    await updateCommunityBasic(communityId.value, basicForm.value)
    ElMessage.success('基本信息已保存')
    await loadCommunity()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    savingBasic.value = false
  }
}

// ─── Tab 2: channels ───────────────────────────────────────────────────────────
const channelList = ref<any[]>([])
const channelDialogVisible = ref(false)
const editingChannel = ref<any>(null)
const savingChannel = ref(false)
const channelForm = ref<any>({ channel_type: 'wechat', is_active: true, config: {} })

const availableChannelTypes = [
  { key: 'wechat', label: '微信公众号' },
  { key: 'hugo',   label: 'Hugo 静态博客' },
  { key: 'csdn',   label: 'CSDN' },
  { key: 'zhihu',  label: '知乎' },
]
function channelTypeLabel(type: string) {
  return availableChannelTypes.find(x => x.key === type)?.label || type
}

function resetChannelConfig() {
  channelForm.value.config = {}
}

function openChannelDialog(ch: any) {
  if (ch) {
    editingChannel.value = ch
    channelForm.value = { channel_type: ch.channel, is_active: ch.enabled, config: { ...ch.config } }
  } else {
    editingChannel.value = null
    channelForm.value = { channel_type: 'wechat', is_active: true, config: {} }
  }
  channelDialogVisible.value = true
}

async function saveChannel() {
  savingChannel.value = true
  try {
    if (editingChannel.value) {
      await updateChannel(editingChannel.value.id, {
        enabled: channelForm.value.is_active,
        config: channelForm.value.config,
      })
    } else {
      await createChannel({
        channel: channelForm.value.channel_type,
        config: channelForm.value.config,
        enabled: true,
      })
    }
    channelDialogVisible.value = false
    ElMessage.success('渠道已保存')
    await loadChannels()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    savingChannel.value = false
  }
}

async function doDeleteChannel(chId: number) {
  await ElMessageBox.confirm('确定删除此渠道配置？', '确认删除', { type: 'warning' })
    .catch(() => { throw new Error('cancel') })
  try {
    await deleteChannel(chId)
    ElMessage.success('已删除')
    await loadChannels()
  } catch (e: any) {
    if (e.message !== 'cancel') ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// ─── Tab 3: email ──────────────────────────────────────────────────────────────
const emailPresets = [
  { key: 'feishu',  label: '飞书',   host: 'smtp.feishu.cn',       port: 465, tls: true },
  { key: 'qq',      label: 'QQ 邮箱', host: 'smtp.qq.com',          port: 465, tls: true },
  { key: '163',     label: '网易163', host: 'smtp.163.com',          port: 465, tls: true },
  { key: 'gmail',   label: 'Gmail',  host: 'smtp.gmail.com',        port: 587, tls: false },
  { key: 'outlook', label: 'Outlook/Office365', host: 'smtp.office365.com', port: 587, tls: false },
]
const selectedEmailPreset = ref('')
const emailForm = ref({
  enabled: false, from_email: '', from_name: 'openGecko 通知',
  smtp_host: '', smtp_port: 465, smtp_use_tls: true, smtp_username: '', smtp_password: '',
})
const savingEmail = ref(false)
const testingEmail = ref(false)
const testEmailResult = ref<{ ok: boolean; msg: string } | null>(null)

function applyEmailPreset(key: string) {
  const p = emailPresets.find(x => x.key === key)
  if (!p) return
  emailForm.value.smtp_host = p.host
  emailForm.value.smtp_port = p.port
  emailForm.value.smtp_use_tls = p.tls
}
function autoDetectPreset() {
  const domain = emailForm.value.from_email.split('@')[1]?.toLowerCase()
  const map: Record<string, string> = {
    'feishu.cn': 'feishu', 'qq.com': 'qq', '163.com': '163',
    'gmail.com': 'gmail', 'outlook.com': 'outlook', 'hotmail.com': 'outlook',
  }
  const p = map[domain]
  if (p) { selectedEmailPreset.value = p; applyEmailPreset(p) }
}
async function saveEmailSettings() {
  savingEmail.value = true
  try {
    await updateEmailSettings(communityId.value, {
      enabled: emailForm.value.enabled,
      provider: 'smtp',
      from_email: emailForm.value.from_email,
      from_name: emailForm.value.from_name,
      smtp: {
        host: emailForm.value.smtp_host,
        port: emailForm.value.smtp_port,
        use_tls: emailForm.value.smtp_use_tls,
        username: emailForm.value.smtp_username,
        password: emailForm.value.smtp_password || undefined,
      },
    })
    ElMessage.success('邮件设置已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    savingEmail.value = false
  }
}
async function sendTestEmail() {
  testingEmail.value = true
  testEmailResult.value = null
  try {
    await testEmailSettings(communityId.value, emailForm.value.from_email)
    testEmailResult.value = { ok: true, msg: '✓ 测试邮件已发送' }
  } catch {
    testEmailResult.value = { ok: false, msg: '✗ 发送失败，请检查配置' }
  } finally {
    testingEmail.value = false
  }
}

// ─── Tab 4: members ────────────────────────────────────────────────────────────
const memberList = ref<any[]>([])
const allUsers = ref<any[]>([])
const selectedAddUserId = ref<number | null>(null)
const selectedAddRole = ref('user')

const availableUsers = computed(() =>
  allUsers.value.filter(u => !memberList.value.some(m => m.id === u.id))
)

async function doAddMember() {
  if (!selectedAddUserId.value) return
  try {
    await addUserToCommunity(communityId.value, selectedAddUserId.value, selectedAddRole.value)
    ElMessage.success('成员已添加')
    selectedAddUserId.value = null
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '添加失败')
  }
}

async function doUpdateRole(userId: number, role: string) {
  try {
    await updateUserRole(communityId.value, userId, role)
    ElMessage.success('角色已更新')
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新失败')
  }
}

async function doRemoveMember(userId: number) {
  await ElMessageBox.confirm('确定移除该成员？', '确认', { type: 'warning' })
    .catch(() => { throw new Error('cancel') })
  try {
    await removeUserFromCommunity(communityId.value, userId)
    ElMessage.success('已移除')
    await loadMembers()
  } catch (e: any) {
    if (e.message !== 'cancel') ElMessage.error(e?.response?.data?.detail || '移除失败')
  }
}

// ─── Tab 5: danger ─────────────────────────────────────────────────────────────
const deleteConfirm = ref('')
const deleting = ref(false)

async function doDeleteCommunity() {
  deleting.value = true
  try {
    await deleteCommunity(communityId.value)
    ElMessage.success('社区已删除')
    communityStore.clearCommunity()
    router.push('/community-overview')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

// ─── loaders ───────────────────────────────────────────────────────────────────
async function loadCommunity() {
  const data = await getCommunity(communityId.value)
  community.value = data
  basicForm.value = {
    name: data.name || '',
    description: data.description || '',
    url: data.url || '',
    logo_url: data.logo_url || '',
  }
}

async function loadChannels() {
  channelList.value = await listChannels()
}

async function loadEmailSettings() {
  try {
    const data = await getEmailSettings(communityId.value)
    if (data) {
      emailForm.value.enabled = data.enabled
      emailForm.value.from_email = data.from_email || ''
      emailForm.value.from_name = data.from_name || 'openGecko 通知'
      emailForm.value.smtp_host = data.smtp?.host || ''
      emailForm.value.smtp_port = data.smtp?.port || 465
      emailForm.value.smtp_use_tls = data.smtp?.use_tls ?? true
      emailForm.value.smtp_username = data.smtp?.username || ''
    }
  } catch { /* not configured */ }
}

async function loadMembers() {
  memberList.value = await getCommunityUsers(communityId.value)
}

onMounted(async () => {
  if (!communityId.value) { router.push('/community'); return }
  await loadCommunity()
  if (authStore.isSuperuser) {
    await Promise.all([loadChannels(), loadEmailSettings()])
  }
  await loadMembers()
  try { allUsers.value = await listAllUsers() } catch { /* ignore */ }
})

watch(() => communityId.value, async (val) => {
  if (val) {
    await loadCommunity()
    await loadMembers()
    if (authStore.isSuperuser) await Promise.all([loadChannels(), loadEmailSettings()])
  }
})
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <el-button text @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <div class="header-title">
        <h1>{{ community?.name || '社区设置' }}</h1>
        <span class="community-slug" v-if="community?.slug">{{ community.slug }}</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">

      <!-- Tab 1: 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <div class="tab-body">
          <el-form ref="basicFormRef" :model="basicForm" :rules="basicRules" label-width="90px" :disabled="!canEditBasic">
            <el-form-item label="社区名称" prop="name">
              <el-input v-model="basicForm.name" maxlength="60" show-word-limit />
            </el-form-item>
            <el-form-item label="唯一标识">
              <el-input :value="community?.slug" disabled />
              <div class="field-hint">唯一标识创建后不可修改</div>
            </el-form-item>
            <el-form-item label="社区描述">
              <el-input v-model="basicForm.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="官网地址">
              <el-input v-model="basicForm.url" placeholder="https://example.com" />
            </el-form-item>
            <el-form-item label="Logo URL">
              <el-input v-model="basicForm.logo_url" />
              <div v-if="basicForm.logo_url" class="logo-preview">
                <img :src="basicForm.logo_url" alt="logo" />
              </div>
            </el-form-item>
            <el-form-item v-if="canEditBasic">
              <el-button type="primary" :loading="savingBasic" @click="saveBasicInfo">保存基本信息</el-button>
            </el-form-item>
          </el-form>
          <el-alert v-if="!canEditBasic" type="info" :closable="false" title="您需要社区管理员权限才能编辑基本信息" />
        </div>
      </el-tab-pane>

      <!-- Tab 2: 渠道配置 (superuser only) -->
      <el-tab-pane v-if="authStore.isSuperuser" label="渠道配置" name="channels">
        <div class="tab-body">
          <div class="tab-toolbar">
            <el-button type="primary" size="small" @click="openChannelDialog(null)">
              <el-icon><Plus /></el-icon> 添加渠道
            </el-button>
          </div>
          <el-table :data="channelList" class="channel-table">
            <el-table-column label="渠道" prop="channel" width="160">
              <template #default="{ row }">
                <el-tag>{{ channelTypeLabel(row.channel) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                  {{ row.enabled ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button text size="small" @click="openChannelDialog(row)">编辑</el-button>
                <el-button text size="small" type="danger" @click="doDeleteChannel(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="channelList.length === 0" description="暂无渠道配置" />
        </div>
      </el-tab-pane>

      <!-- Tab 3: 邮件设置 (superuser only) -->
      <el-tab-pane v-if="authStore.isSuperuser" label="邮件设置" name="email">
        <div class="tab-body">
          <el-form label-width="110px">
            <el-form-item label="启用邮件">
              <el-switch v-model="emailForm.enabled" />
            </el-form-item>
            <template v-if="emailForm.enabled">
              <el-form-item label="服务商预设">
                <el-select v-model="selectedEmailPreset" placeholder="选择后自动填充" clearable @change="applyEmailPreset">
                  <el-option v-for="p in emailPresets" :key="p.key" :label="p.label" :value="p.key" />
                </el-select>
              </el-form-item>
              <el-form-item label="发件人邮箱">
                <el-input v-model="emailForm.from_email" @blur="autoDetectPreset" />
              </el-form-item>
              <el-form-item label="发件人名称">
                <el-input v-model="emailForm.from_name" />
              </el-form-item>
              <el-form-item label="SMTP 服务器">
                <el-input v-model="emailForm.smtp_host" />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number v-model="emailForm.smtp_port" :min="1" :max="65535" style="width:130px" />
                <el-switch v-model="emailForm.smtp_use_tls" active-text="TLS" style="margin-left:16px" />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="emailForm.smtp_username" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="emailForm.smtp_password" type="password" show-password placeholder="留空则不更改" />
              </el-form-item>
              <el-form-item label="">
                <div class="email-action-row">
                  <el-button :loading="savingEmail" type="primary" @click="saveEmailSettings">保存邮件设置</el-button>
                  <el-button :loading="testingEmail" @click="sendTestEmail">发送测试邮件</el-button>
                  <span v-if="testEmailResult" class="test-result" :class="testEmailResult.ok ? 'ok' : 'fail'">
                    {{ testEmailResult.msg }}
                  </span>
                </div>
              </el-form-item>
            </template>
            <el-form-item v-if="!emailForm.enabled">
              <el-button type="primary" :loading="savingEmail" @click="saveEmailSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- Tab 4: 成员管理 -->
      <el-tab-pane label="成员管理" name="members">
        <div class="tab-body">
          <div class="tab-toolbar" v-if="canEditBasic">
            <el-select
              v-model="selectedAddUserId"
              filterable clearable
              placeholder="搜索用户添加成员"
              style="width:240px"
            >
              <el-option v-for="u in availableUsers" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
            </el-select>
            <el-select v-model="selectedAddRole" style="width:110px">
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
            </el-select>
            <el-button type="primary" size="small" :disabled="!selectedAddUserId" @click="doAddMember">添加</el-button>
          </div>
          <el-table :data="memberList">
            <el-table-column label="用户名" prop="username" />
            <el-table-column label="邮箱" prop="email" />
            <el-table-column label="角色" width="160">
              <template #default="{ row }">
                <el-select
                  v-if="canEditBasic && row.id !== authStore.user?.id"
                  :model-value="row.role"
                  size="small"
                  style="width:110px"
                  @change="(v: string) => doUpdateRole(row.id, v)"
                >
                  <el-option label="管理员" value="admin" />
                  <el-option label="普通用户" value="user" />
                </el-select>
                <el-tag v-else size="small">{{ row.role === 'admin' ? '管理员' : '普通用户' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" v-if="canEditBasic">
              <template #default="{ row }">
                <el-button
                  v-if="row.id !== authStore.user?.id"
                  text size="small" type="danger"
                  @click="doRemoveMember(row.id)"
                >移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Tab 5: 危险操作 (superuser only) -->
      <el-tab-pane v-if="authStore.isSuperuser" label="危险操作" name="danger">
        <div class="tab-body">
          <div class="danger-zone">
            <div class="danger-header">
              <el-icon color="#ef4444"><WarningFilled /></el-icon>
              <span>危险操作区域</span>
            </div>
            <p class="danger-desc">删除社区将清除所有相关数据，包括内容、成员记录、渠道配置等，且不可恢复。</p>
            <el-divider />
            <p class="confirm-label">请输入社区标识 <code>{{ community?.slug }}</code> 以确认删除：</p>
            <div class="danger-row">
              <el-input v-model="deleteConfirm" placeholder="输入 slug 确认" style="width:240px" />
              <el-button type="danger" :disabled="deleteConfirm !== community?.slug" :loading="deleting" @click="doDeleteCommunity">
                永久删除社区
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

    </el-tabs>

    <!-- Channel dialog -->
    <el-dialog v-model="channelDialogVisible" :title="editingChannel ? '编辑渠道' : '添加渠道'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="渠道类型" v-if="!editingChannel">
          <el-select v-model="channelForm.channel_type" @change="resetChannelConfig">
            <el-option v-for="d in availableChannelTypes" :key="d.key" :label="d.label" :value="d.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="channelForm.is_active" />
        </el-form-item>
        <template v-if="channelForm.channel_type === 'wechat'">
          <el-form-item label="AppID">
            <el-input v-model="channelForm.config.app_id" />
          </el-form-item>
          <el-form-item label="AppSecret">
            <el-input v-model="channelForm.config.app_secret" type="password" show-password />
          </el-form-item>
        </template>
        <template v-else-if="channelForm.channel_type === 'hugo'">
          <el-form-item label="仓库路径">
            <el-input v-model="channelForm.config.repo_path" />
          </el-form-item>
          <el-form-item label="内容目录">
            <el-input v-model="channelForm.config.content_dir" />
          </el-form-item>
        </template>
        <template v-else>
          <el-alert type="info" :closable="false" title="该渠道使用复制粘贴方式发布，无需额外配置字段。" />
        </template>
      </el-form>
      <template #footer>
        <el-button @click="channelDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingChannel" @click="saveChannel">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<style scoped>
.settings-page {
  padding: 24px 32px;
  max-width: 860px;
  margin: 0 auto;
}
.settings-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}
.header-title { display: flex; align-items: baseline; gap: 10px; }
.header-title h1 { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0; }
.community-slug {
  font-size: 13px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}
.settings-tabs { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.06); overflow: hidden; }
.tab-body { padding: 24px; }
.tab-toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }
.field-hint { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.channel-table { width: 100%; }
.logo-preview { margin-top: 8px; }
.logo-preview img { height: 40px; border-radius: 4px; border: 1px solid #e2e8f0; }
.email-action-row { display: flex; align-items: center; gap: 10px; }
.test-result { font-size: 12px; }
.test-result.ok { color: #22c55e; }
.test-result.fail { color: #ef4444; }
/* danger zone */
.danger-zone {
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 20px;
  background: #fff5f5;
}
.danger-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #ef4444;
  margin-bottom: 8px;
}
.danger-desc { font-size: 13px; color: #64748b; margin: 0 0 4px; }
.confirm-label { font-size: 13px; color: #475569; margin-bottom: 10px; }
.confirm-label code { background: #fef2f2; padding: 1px 5px; border-radius: 3px; font-weight: 600; }
.danger-row { display: flex; gap: 10px; align-items: center; }
</style>