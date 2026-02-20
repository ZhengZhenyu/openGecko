<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { InfoFilled, Close, CircleCheck, Remove } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useCommunityStore } from '@/stores/community'
import {
  createCommunity,
  addUserToCommunity,
  getEmailSettings,
  updateEmailSettings,
  testEmailSettings,
} from '@/api/community'
import { createChannel } from '@/api/channel'
import { listAllUsers } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

// ─── steps ───────────────────────────────────────────────────────────────────
const currentStep = ref(0)
const saving = ref(false)

// ─── step 0: basic info ───────────────────────────────────────────────────────
const basicFormRef = ref()
const basicForm = ref({ name: '', slug: '', description: '', url: '', logo_url: '' })
const createdCommunity = ref<any>(null)

const basicRules = {
  name: [{ required: true, message: '请填写社区名称', trigger: 'blur' }],
  slug: [
    { required: true, message: '请填写唯一标识', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '只允许小写字母、数字和连字符', trigger: 'blur' },
  ],
}

// auto-generate slug from name (pinyin-like simple transform)
function genSlug(name: string) {
  return name
    .toLowerCase()
    .replace(/[\s_]+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .slice(0, 40)
}

watch(() => basicForm.value.name, (val) => {
  if (!basicForm.value.slug) {
    basicForm.value.slug = genSlug(val)
  }
})

// ─── step 1: channels ─────────────────────────────────────────────────────────
const channelDefs = [
  { key: 'wechat', label: '微信公众号' },
  { key: 'hugo',   label: 'Hugo 静态博客' },
  { key: 'csdn',   label: 'CSDN' },
  { key: 'zhihu',  label: '知乎' },
]

const channels = ref<Record<string, { enabled: boolean; config: Record<string, string> }>>({
  wechat: { enabled: false, config: { app_id: '', app_secret: '' } },
  hugo:   { enabled: false, config: { repo_path: '', content_dir: 'content/posts' } },
  csdn:   { enabled: false, config: {} },
  zhihu:  { enabled: false, config: {} },
})

// ─── step 2: email ────────────────────────────────────────────────────────────
const emailPresets = [
  { key: 'feishu',  label: '飞书',   host: 'smtp.feishu.cn',       port: 465, tls: true },
  { key: 'qq',      label: 'QQ 邮箱', host: 'smtp.qq.com',          port: 465, tls: true },
  { key: '163',     label: '网易163', host: 'smtp.163.com',          port: 465, tls: true },
  { key: 'gmail',   label: 'Gmail',  host: 'smtp.gmail.com',        port: 587, tls: false },
  { key: 'outlook', label: 'Outlook/Office365', host: 'smtp.office365.com', port: 587, tls: false },
]

const selectedEmailPreset = ref('')
const emailForm = ref({
  enabled: false,
  from_email: '',
  from_name: 'openGecko 通知',
  smtp: { host: '', port: 465, use_tls: true, username: '', password: '' },
})
const testingEmail = ref(false)
const testEmailResult = ref<{ ok: boolean; msg: string } | null>(null)

function applyEmailPreset(key: string) {
  const p = emailPresets.find(x => x.key === key)
  if (!p) return
  emailForm.value.smtp.host = p.host
  emailForm.value.smtp.port = p.port
  emailForm.value.smtp.use_tls = p.tls
}

function autoDetectPreset() {
  const domain = emailForm.value.from_email.split('@')[1]?.toLowerCase()
  if (!domain) return
  const mapping: Record<string, string> = {
    'feishu.cn': 'feishu', 'qq.com': 'qq', '163.com': '163',
    'gmail.com': 'gmail', 'outlook.com': 'outlook', 'hotmail.com': 'outlook',
  }
  const preset = mapping[domain]
  if (preset) {
    selectedEmailPreset.value = preset
    applyEmailPreset(preset)
  }
}

async function sendTestEmail() {
  if (!createdCommunity.value) return
  testingEmail.value = true
  testEmailResult.value = null
  try {
    await testEmailSettings(createdCommunity.value.id, emailForm.value.from_email)
    testEmailResult.value = { ok: true, msg: '✓ 测试邮件已发送' }
  } catch {
    testEmailResult.value = { ok: false, msg: '✗ 发送失败，请检查配置' }
  } finally {
    testingEmail.value = false
  }
}

// ─── step 3: invite members ───────────────────────────────────────────────────
const allUsers = ref<any[]>([])
const selectedInviteUserId = ref<number | null>(null)
const selectedInviteRole = ref('user')
const inviteList = ref<{ userId: number; label: string; role: string }[]>([])

const availableUsers = computed(() =>
  allUsers.value.filter(u => !inviteList.value.some(i => i.userId === u.id))
)

function addToInviteList() {
  if (!selectedInviteUserId.value) return
  const u = allUsers.value.find(x => x.id === selectedInviteUserId.value)
  if (!u) return
  inviteList.value.push({
    userId: u.id,
    label: `${u.username} (${u.email})`,
    role: selectedInviteRole.value,
  })
  selectedInviteUserId.value = null
  selectedInviteRole.value = 'user'
}

// ─── summary ──────────────────────────────────────────────────────────────────
const summaryItems = ref({
  basic: false,
  channels: false,
  channelCount: 0,
  email: false,
  members: false,
})

// ─── navigation ───────────────────────────────────────────────────────────────
async function nextStep() {
  if (currentStep.value === 0) {
    await doCreateCommunity()
  } else if (currentStep.value === 1) {
    await doSaveChannels()
    currentStep.value++
  } else if (currentStep.value === 2) {
    await doSaveEmail()
    currentStep.value++
  }
}

function skipStep() {
  currentStep.value++
}

function prevStep() {
  if (currentStep.value > 0) currentStep.value--
}

async function finishWizard() {
  saving.value = true
  try {
    // invite members
    if (inviteList.value.length > 0 && createdCommunity.value) {
      for (const item of inviteList.value) {
        await addUserToCommunity(createdCommunity.value.id, item.userId, item.role)
      }
      summaryItems.value.members = true
    }
    currentStep.value = 4
  } catch (e: any) {
    ElMessage.error('邀请成员失败：' + (e?.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function goToCommunity() {
  if (createdCommunity.value) {
    communityStore.setCurrentCommunity(createdCommunity.value.id)
  }
  router.push('/community')
}

// ─── actions ──────────────────────────────────────────────────────────────────
async function doCreateCommunity() {
  const valid = await basicFormRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = await createCommunity({
      name: basicForm.value.name,
      slug: basicForm.value.slug,
      description: basicForm.value.description || undefined,
      url: basicForm.value.url || undefined,
      logo_url: basicForm.value.logo_url || undefined,
    })
    createdCommunity.value = data
    summaryItems.value.basic = true
    currentStep.value++
  } catch (e: any) {
    ElMessage.error('创建社区失败：' + (e?.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function doSaveChannels() {
  if (!createdCommunity.value) return
  saving.value = true
  let count = 0
  try {
    for (const def of channelDefs) {
      const ch = channels.value[def.key]
      if (!ch.enabled) continue
      await createChannel({
        channel: def.key,
        config: ch.config,
        enabled: true,
      })
      count++
    }
    if (count > 0) {
      summaryItems.value.channels = true
      summaryItems.value.channelCount = count
    }
  } catch (e: any) {
    ElMessage.warning('部分渠道保存失败：' + (e?.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function doSaveEmail() {
  if (!createdCommunity.value || !emailForm.value.enabled) return
  saving.value = true
  try {
    await updateEmailSettings(createdCommunity.value.id, {
      enabled: true,
      provider: 'smtp',
      from_email: emailForm.value.from_email,
      from_name: emailForm.value.from_name,
      smtp: {
        host: emailForm.value.smtp.host,
        port: emailForm.value.smtp.port,
        use_tls: emailForm.value.smtp.use_tls,
        username: emailForm.value.smtp.username,
        password: emailForm.value.smtp.password,
      },
    })
    summaryItems.value.email = true
  } catch (e: any) {
    ElMessage.warning('邮件设置保存失败：' + (e?.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

// ─── init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    allUsers.value = await listAllUsers()
  } catch { /* ignore */ }
})
</script>

<template>
  <div class="wizard-page">
    <div class="wizard-container">
      <!-- Header -->
      <div class="wizard-header">
        <img src="/openGecko-Horizontal.png" alt="openGecko" class="wizard-logo" />
        <h1 class="wizard-title">创建新社区</h1>
        <p class="wizard-sub">按照引导完成社区的基础配置，随时可跳过选填步骤</p>
      </div>

      <!-- Steps bar -->
      <el-steps :active="currentStep" align-center finish-status="success" class="wizard-steps">
        <el-step title="基本信息" />
        <el-step title="渠道配置" />
        <el-step title="邮件设置" />
        <el-step title="邀请成员" />
        <el-step title="完成" />
      </el-steps>

      <!-- Step content -->
      <div class="wizard-body">

        <!-- Step 0: 基本信息 -->
        <div v-if="currentStep === 0" class="step-panel">
          <h2 class="step-title">填写社区基本信息</h2>
          <el-form ref="basicFormRef" :model="basicForm" :rules="basicRules" label-width="90px" size="large">
            <el-form-item label="社区名称" prop="name">
              <el-input v-model="basicForm.name" placeholder="如：CNCF Kubernetes SIG" maxlength="60" show-word-limit />
            </el-form-item>
            <el-form-item label="唯一标识" prop="slug">
              <el-input v-model="basicForm.slug" placeholder="英文标识，如 kubernetes-sig（创建后不可修改）" maxlength="40">
                <template #prepend>opengecko.io/</template>
              </el-input>
            </el-form-item>
            <el-form-item label="社区描述">
              <el-input v-model="basicForm.description" type="textarea" :rows="3" placeholder="简要描述社区的定位和目标（可选）" />
            </el-form-item>
            <el-form-item label="官网地址">
              <el-input v-model="basicForm.url" placeholder="https://example.com（可选）" />
            </el-form-item>
            <el-form-item label="Logo URL">
              <el-input v-model="basicForm.logo_url" placeholder="Logo 图片链接（可选）" />
            </el-form-item>
          </el-form>
        </div>

        <!-- Step 1: 渠道配置 -->
        <div v-if="currentStep === 1" class="step-panel">
          <h2 class="step-title">配置发布渠道 <span class="optional-tag">可跳过</span></h2>
          <p class="step-desc">超管专属：配置后社区管理员可将内容发布到对应平台。</p>
          <div class="channel-list">
            <div v-for="ch in channelDefs" :key="ch.key" class="channel-block">
              <div class="channel-block-header">
                <div class="channel-label-row">
                  <el-switch v-model="channels[ch.key].enabled" size="small" />
                  <span class="ch-name">{{ ch.label }}</span>
                </div>
              </div>
              <div v-if="channels[ch.key].enabled" class="channel-fields">
                <template v-if="ch.key === 'wechat'">
                  <el-form-item label="AppID">
                    <el-input v-model="channels.wechat.config.app_id" placeholder="AppID" />
                  </el-form-item>
                  <el-form-item label="AppSecret">
                    <el-input v-model="channels.wechat.config.app_secret" type="password" show-password placeholder="AppSecret" />
                  </el-form-item>
                </template>
                <template v-else-if="ch.key === 'hugo'">
                  <el-form-item label="仓库路径">
                    <el-input v-model="channels.hugo.config.repo_path" placeholder="Hugo 仓库本地路径" />
                  </el-form-item>
                  <el-form-item label="内容目录">
                    <el-input v-model="channels.hugo.config.content_dir" placeholder="content/posts" />
                  </el-form-item>
                </template>
                <template v-else>
                  <p class="hint-text">{{ ch.label }} 使用复制粘贴方式发布，无需额外配置。</p>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: 邮件设置 -->
        <div v-if="currentStep === 2" class="step-panel">
          <h2 class="step-title">配置 SMTP 邮件 <span class="optional-tag">可跳过</span></h2>
          <p class="step-desc">超管专属：配置后系统可发送邀请邮件和通知。</p>
          <el-form label-width="110px" size="default">
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
                <el-input v-model="emailForm.from_email" placeholder="noreply@example.com" @blur="autoDetectPreset" />
              </el-form-item>
              <el-form-item label="发件人名称">
                <el-input v-model="emailForm.from_name" placeholder="openGecko 通知" />
              </el-form-item>
              <el-form-item label="SMTP 服务器">
                <el-input v-model="emailForm.smtp.host" placeholder="smtp.qq.com" />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number v-model="emailForm.smtp.port" :min="1" :max="65535" style="width:130px" />
                <el-switch v-model="emailForm.smtp.use_tls" active-text="TLS" style="margin-left:16px" />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="emailForm.smtp.username" placeholder="SMTP 登录用户名" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="emailForm.smtp.password" type="password" show-password placeholder="SMTP 密码或授权码" />
              </el-form-item>
              <el-form-item label="">
                <el-button :loading="testingEmail" @click="sendTestEmail">发送测试邮件</el-button>
                <span v-if="testEmailResult" class="test-result" :class="testEmailResult.ok ? 'ok' : 'fail'">
                  {{ testEmailResult.msg }}
                </span>
              </el-form-item>
            </template>
          </el-form>
        </div>

        <!-- Step 3: 邀请成员 -->
        <div v-if="currentStep === 3" class="step-panel">
          <h2 class="step-title">邀请成员 <span class="optional-tag">可跳过</span></h2>
          <p class="step-desc">为新社区邀请成员，建议至少邀请一位社区管理员负责日常运营。</p>
          <div class="invite-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>从已注册用户中选择并分配角色。被邀请者立即加入社区。</span>
          </div>
          <div class="invite-row">
            <el-select
              v-model="selectedInviteUserId"
              filterable
              clearable
              placeholder="搜索用户（用户名/邮箱）"
              style="width: 280px"
            >
              <el-option
                v-for="u in availableUsers"
                :key="u.id"
                :label="`${u.username} (${u.email})`"
                :value="u.id"
              />
            </el-select>
            <el-select v-model="selectedInviteRole" style="width: 120px">
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
            </el-select>
            <el-button type="primary" :disabled="!selectedInviteUserId" @click="addToInviteList">添加</el-button>
          </div>
          <div v-if="inviteList.length > 0" class="invite-table">
            <div v-for="(item, idx) in inviteList" :key="idx" class="invite-item">
              <span class="invite-name">{{ item.label }}</span>
              <el-tag :type="item.role === 'admin' ? 'warning' : 'info'" size="small">
                {{ item.role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
              <el-icon class="remove-icon" @click="inviteList.splice(idx, 1)"><Close /></el-icon>
            </div>
          </div>
          <p v-else class="empty-hint">暂未添加任何成员，可直接跳过。</p>
        </div>

        <!-- Step 4: 完成 -->
        <div v-if="currentStep === 4" class="step-panel summary-panel">
          <div class="success-icon">🎉</div>
          <h2 class="step-title">社区「{{ createdCommunity?.name }}」已创建！</h2>
          <p class="step-desc">以下是本次配置摘要：</p>
          <div class="summary-list">
            <div class="summary-item" :class="summaryItems.basic ? 'done' : 'skip'">
              <el-icon><CircleCheck v-if="summaryItems.basic" /><Remove v-else /></el-icon>
              基本信息：已保存
            </div>
            <div class="summary-item" :class="summaryItems.channels ? 'done' : 'skip'">
              <el-icon><CircleCheck v-if="summaryItems.channels" /><Remove v-else /></el-icon>
              渠道配置：{{ summaryItems.channels ? '已配置 ' + summaryItems.channelCount + ' 个渠道' : '已跳过' }}
            </div>
            <div class="summary-item" :class="summaryItems.email ? 'done' : 'skip'">
              <el-icon><CircleCheck v-if="summaryItems.email" /><Remove v-else /></el-icon>
              邮件设置：{{ summaryItems.email ? '已配置' : '已跳过' }}
            </div>
            <div class="summary-item" :class="summaryItems.members ? 'done' : 'skip'">
              <el-icon><CircleCheck v-if="summaryItems.members" /><Remove v-else /></el-icon>
              成员邀请：{{ summaryItems.members ? '已邀请 ' + inviteList.length + ' 位成员' : '已跳过' }}
            </div>
          </div>
        </div>

      </div>

      <!-- Footer buttons -->
      <div class="wizard-footer">
        <el-button v-if="currentStep > 0 && currentStep < 4" @click="prevStep">上一步</el-button>
        <div class="footer-right">
          <el-button v-if="currentStep < 3 && currentStep > 0" @click="skipStep">跳过</el-button>
          <el-button
            v-if="currentStep < 3"
            type="primary"
            :loading="saving"
            @click="nextStep"
          >
            {{ currentStep === 0 ? '创建社区并继续' : '下一步' }}
          </el-button>
          <el-button
            v-if="currentStep === 3"
            type="primary"
            :loading="saving"
            @click="finishWizard"
          >
            完成配置
          </el-button>
          <el-button v-if="currentStep === 4" type="primary" @click="goToCommunity">
            进入社区工作台
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wizard-page {
  min-height: 100vh;
  background: #f1f5f9;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 40px 16px 80px;
}
.wizard-container {
  width: 100%;
  max-width: 760px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0,0,0,.08);
  overflow: hidden;
}
.wizard-header {
  padding: 36px 40px 24px;
  text-align: center;
  border-bottom: 1px solid #e2e8f0;
}
.wizard-logo {
  height: 32px;
  margin-bottom: 12px;
}
.wizard-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px;
}
.wizard-sub {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}
.wizard-steps {
  padding: 24px 40px 0;
}
.wizard-body {
  padding: 28px 40px 8px;
  min-height: 320px;
}
.wizard-footer {
  padding: 20px 40px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #e2e8f0;
  margin-top: 12px;
}
.footer-right {
  display: flex;
  gap: 10px;
}
.step-panel {}
.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 6px;
}
.step-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 18px;
}
.optional-tag {
  font-size: 11px;
  font-weight: 400;
  color: #94a3b8;
  margin-left: 8px;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  vertical-align: middle;
}
/* channels */
.channel-list { display: flex; flex-direction: column; gap: 12px; }
.channel-block {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
}
.channel-block-header { margin-bottom: 4px; }
.channel-label-row { display: flex; align-items: center; gap: 10px; }
.ch-name { font-size: 14px; font-weight: 500; color: #334155; }
.channel-fields { margin-top: 12px; }
.hint-text { font-size: 13px; color: #94a3b8; margin: 4px 0 0; }
/* invite */
.invite-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 14px;
}
.invite-row { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; }
.invite-table { display: flex; flex-direction: column; gap: 6px; }
.invite-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: #f8fafc;
  border-radius: 6px;
}
.invite-name { flex: 1; font-size: 13px; color: #334155; }
.remove-icon { cursor: pointer; color: #94a3b8; }
.remove-icon:hover { color: #ef4444; }
.empty-hint { font-size: 13px; color: #94a3b8; text-align: center; padding: 20px 0; }
/* email test */
.test-result { font-size: 12px; margin-left: 10px; }
.test-result.ok { color: #22c55e; }
.test-result.fail { color: #ef4444; }
/* summary */
.summary-panel { text-align: center; }
.success-icon { font-size: 56px; margin-bottom: 8px; }
.summary-list {
  display: inline-flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
  text-align: left;
}
.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.summary-item.done { color: #22c55e; }
.summary-item.skip { color: #94a3b8; }
</style>
