<template>
  <div class="community-manage">
    <div class="page-title">
      <div>
        <h2>社区管理</h2>
        <p class="subtitle">管理所有社区和成员</p>
      </div>
      <el-button v-if="isSuperuser" type="primary" :icon="Plus" @click="showCreateDialog">新建社区</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="community in communities" :key="community.id">
        <el-card class="community-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="community-title">
                <span class="name">{{ community.name }}</span>
                <el-tag v-if="!community.is_active" type="danger" size="small">已停用</el-tag>
              </div>
              <el-dropdown @command="(cmd: string) => handleCommunityAction(cmd, community)">
                <el-icon class="more-icon"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item v-if="isSuperuser || community.role === 'admin'" command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="channels">渠道管理</el-dropdown-item>
                    <el-dropdown-item v-if="isSuperuser || community.role === 'admin'" command="email">邮件设置</el-dropdown-item>
                    <el-dropdown-item v-if="isSuperuser" command="members">成员管理</el-dropdown-item>
                    <el-dropdown-item v-if="isSuperuser || community.role === 'admin'" command="toggle">{{ community.is_active ? '停用' : '启用' }}</el-dropdown-item>
                    <el-dropdown-item v-if="isSuperuser" command="delete" divided style="color: #f56c6c">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          <div class="community-info">
            <p class="slug"><el-icon><Link /></el-icon> {{ community.slug }}</p>
            <p v-if="community.url" class="url">
              <a :href="community.url" target="_blank" rel="noopener">{{ community.url }}</a>
            </p>
            <p class="desc">{{ community.description || '暂无描述' }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Create/Edit Community Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑社区' : '新建社区'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="communityForm"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="communityForm.name" placeholder="社区名称" />
        </el-form-item>
        <el-form-item label="标识" prop="slug">
          <el-input
            v-model="communityForm.slug"
            placeholder="英文标识 (如 my-community)"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="communityForm.description"
            type="textarea"
            :rows="3"
            placeholder="社区描述"
          />
        </el-form-item>
        <el-form-item label="项目地址">
          <el-input v-model="communityForm.url" placeholder="社区官网或项目仓库地址（可选）" />
        </el-form-item>
        <el-form-item label="Logo URL">
          <el-input v-model="communityForm.logo_url" placeholder="Logo 图片地址（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Members Management Dialog -->
    <el-dialog
      v-model="membersDialogVisible"
      :title="`成员管理 - ${selectedCommunity?.name || ''}`"
      width="700px"
    >
      <div class="members-header">
        <el-select
          v-model="selectedUserId"
          filterable
          placeholder="搜索用户并添加"
          style="width: 280px"
        >
          <el-option
            v-for="u in availableUsers"
            :key="u.id"
            :label="`${u.username} (${u.email})`"
            :value="u.id"
          />
        </el-select>
        <el-button type="primary" :disabled="!selectedUserId" @click="handleAddMember">
          添加成员
        </el-button>
      </div>

      <el-table :data="communityUsers" stripe style="margin-top: 16px">
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            <template v-if="row.is_superuser">
              <el-tag type="danger" size="small">超级管理员</el-tag>
            </template>
            <template v-else>
              <el-select
                :model-value="row.role"
                size="small"
                style="width: 110px"
                @change="(val: string) => handleRoleChange(row, val)"
              >
                <el-option label="管理员" value="admin" />
                <el-option label="普通用户" value="user" />
              </el-select>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-popconfirm
              title="确定移除该成员？"
              @confirm="handleRemoveMember(row.id)"
              :disabled="row.is_superuser"
            >
              <template #reference>
                <el-button size="small" type="danger" :disabled="row.is_superuser">
                  移除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Channel Management Dialog -->
    <el-dialog
      v-model="channelsDialogVisible"
      :title="`渠道管理 - ${selectedCommunity?.name || ''}`"
      width="750px"
    >
      <div class="channels-header">
        <el-select v-model="newChannelType" placeholder="选择渠道类型" style="width: 200px">
          <el-option
            v-for="ch in availableChannelTypes"
            :key="ch.value"
            :label="ch.label"
            :value="ch.value"
          />
        </el-select>
        <el-button type="primary" :disabled="!newChannelType" @click="showAddChannelForm">
          添加渠道
        </el-button>
      </div>

      <el-table :data="channelConfigs" stripe style="margin-top: 16px">
        <el-table-column label="渠道" width="140">
          <template #default="{ row }">
            {{ channelLabelMap[row.channel] || row.channel }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.enabled"
              @change="(val: boolean) => handleToggleChannel(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="配置" min-width="200">
          <template #default="{ row }">
            <span v-if="Object.keys(row.config).length === 0" class="hint-text">未配置</span>
            <span v-else class="hint-text">已配置 {{ Object.keys(row.config).length }} 项</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="showEditChannelForm(row)">编辑</el-button>
            <el-popconfirm title="确定删除该渠道？" @confirm="handleDeleteChannel(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Channel Config Edit Dialog -->
    <el-dialog
      v-model="channelFormVisible"
      :title="editingChannel ? '编辑渠道配置' : '添加渠道'"
      width="500px"
    >
      <el-form label-width="100px" size="default">
        <el-form-item label="渠道类型">
          <el-input :model-value="channelLabelMap[channelForm.channel] || channelForm.channel" disabled />
        </el-form-item>

        <template v-if="channelForm.channel === 'wechat'">
          <el-form-item label="AppID">
            <el-input v-model="channelForm.config.app_id" placeholder="微信公众号 AppID" />
          </el-form-item>
          <el-form-item label="AppSecret">
            <el-input
              v-model="channelForm.config.app_secret"
              type="password"
              show-password
              placeholder="微信公众号 AppSecret"
              @focus="handleSecretFocus('app_secret')"
            />
            <div v-if="isSecretMasked(channelForm.config.app_secret)" class="secret-hint">已配置，留空则保持不变</div>
          </el-form-item>
        </template>

        <template v-else-if="channelForm.channel === 'hugo'">
          <el-form-item label="仓库路径">
            <el-input v-model="channelForm.config.repo_path" placeholder="Hugo 仓库本地路径" />
          </el-form-item>
          <el-form-item label="内容目录">
            <el-input v-model="channelForm.config.content_dir" placeholder="如 content/posts" />
          </el-form-item>
        </template>

        <template v-else-if="channelForm.channel === 'csdn'">
          <el-form-item label="说明">
            <span class="hint-text">CSDN 使用复制粘贴方式发布，无需额外配置</span>
          </el-form-item>
        </template>

        <template v-else-if="channelForm.channel === 'zhihu'">
          <el-form-item label="说明">
            <span class="hint-text">知乎使用复制粘贴方式发布，无需额外配置</span>
          </el-form-item>
        </template>

        <el-form-item label="启用">
          <el-switch v-model="channelForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="channelFormVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveChannel">保存</el-button>
      </template>
    </el-dialog>

    <!-- Email Settings Dialog -->
    <el-dialog
      v-model="emailSettingsVisible"
      :title="`邮件设置 - ${selectedCommunity?.name || ''}`"
      width="600px"
    >
      <el-form
        ref="emailFormRef"
        :model="emailForm"
        label-width="120px"
      >
        <el-form-item label="启用邮件">
          <el-switch v-model="emailForm.enabled" />
        </el-form-item>

        <el-divider content-position="left">SMTP 配置</el-divider>

        <el-form-item label="快速配置">
          <el-select
            v-model="selectedEmailTemplate"
            placeholder="选择邮箱服务商模板（可选）"
            @change="applyEmailTemplate"
            clearable
            style="width: 100%"
          >
            <el-option label="飞书邮箱" value="feishu" />
            <el-option label="QQ邮箱" value="qq" />
            <el-option label="163邮箱" value="163" />
            <el-option label="Gmail" value="gmail" />
            <el-option label="Outlook" value="outlook" />
          </el-select>
        </el-form-item>

        <el-form-item label="发件人邮箱" prop="from_email" required>
          <el-input v-model="emailForm.from_email" placeholder="your-email@example.com" />
        </el-form-item>

        <el-form-item label="发件人名称">
          <el-input v-model="emailForm.from_name" placeholder="社区名称（可选）" />
        </el-form-item>

        <el-form-item label="回复邮箱">
          <el-input v-model="emailForm.reply_to" placeholder="回复地址（可选）" />
        </el-form-item>

        <el-form-item label="SMTP 服务器" prop="smtp.host" required>
          <el-input v-model="emailForm.smtp.host" placeholder="smtp.example.com" />
        </el-form-item>

        <el-form-item label="SMTP 端口" prop="smtp.port" required>
          <el-input-number v-model="emailForm.smtp.port" :min="1" :max="65535" />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            常用端口：465 (SSL/TLS) 或 587 (STARTTLS)
          </div>
        </el-form-item>

        <el-form-item label="用户名">
          <div style="display: flex; gap: 8px; align-items: flex-start; flex-direction: column; width: 100%;">
            <el-input v-model="emailForm.smtp.username" placeholder="留空自动使用发件人邮箱" style="width: 100%;" />
            <el-button 
              v-if="emailForm.from_email && !emailForm.smtp.username" 
              size="small" 
              text
              @click="emailForm.smtp.username = emailForm.from_email"
            >
              使用发件人邮箱 ({{ emailForm.from_email }})
            </el-button>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            大多数邮箱服务的用户名就是完整邮箱地址，留空则自动使用上面的发件人邮箱
          </div>
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="emailForm.smtp.password"
            type="password"
            show-password
            placeholder="SMTP密码或专用密码"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            <template v-if="emailForm.smtp.password">
              <span style="color: #67c23a;">✓ 密码已填写</span>。点击小眼睛图标可查看密码
            </template>
            <template v-else>
              <span style="color: #f56c6c;">• 请填写密码</span>
            </template>
            <div style="margin-top: 4px;">
              部分邮箱需要使用专用密码而非登录密码
            </div>
          </div>
        </el-form-item>

        <el-form-item label="加密方式">
          <el-radio-group v-model="emailForm.smtp.port" @change="handlePortChange">
            <el-radio :label="465">SSL/TLS (端口465，推荐)</el-radio>
            <el-radio :label="587">STARTTLS (端口587)</el-radio>
          </el-radio-group>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            端口465会自动使用SSL加密连接
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%;">
          <el-button @click="handleTestEmailSettings" :loading="emailTesting" :disabled="!emailForm.smtp.host || !emailForm.from_email">
            测试配置
          </el-button>
          <div>
            <el-button @click="emailSettingsVisible = false">取消</el-button>
            <el-button type="primary" @click="handleSaveEmailSettings" :loading="emailSaving">保存</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, MoreFilled, Link } from '@element-plus/icons-vue'
import type { Community } from '../stores/auth'
import { useAuthStore } from '../stores/auth'
import {
  getCommunities,
  createCommunity,
  updateCommunity,
  deleteCommunity,
  getCommunityUsers,
  addUserToCommunity,
  removeUserFromCommunity,
  updateUserRole,
  getEmailSettings,
  updateEmailSettings,
  testEmailSettings,
  type CommunityUser,
  type EmailSettings,
  type EmailSettingsOut,
} from '../api/community'
import {
  listChannels,
  createChannel,
  updateChannel,
  deleteChannel,
  type ChannelConfig,
} from '../api/channel'
import { listAllUsers } from '../api/auth'
import type { User } from '../stores/auth'

const authStore = useAuthStore()
const isSuperuser = computed(() => authStore.isSuperuser)

const communities = ref<Community[]>([])
const dialogVisible = ref(false)
const membersDialogVisible = ref(false)
const channelsDialogVisible = ref(false)
const channelFormVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const communityForm = ref({
  name: '',
  slug: '',
  description: '',
  url: '',
  logo_url: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入社区名称', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入社区标识', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' },
  ],
}

const selectedCommunity = ref<Community | null>(null)
const communityUsers = ref<CommunityUser[]>([])
const allUsers = ref<User[]>([])
const selectedUserId = ref<number | null>(null)

const availableUsers = computed(() => {
  const memberIds = new Set(communityUsers.value.map((u) => u.id))
  return allUsers.value.filter((u) => !memberIds.has(u.id))
})

// ── Channel management ──────────────────────────────────────────────
const channelConfigs = ref<ChannelConfig[]>([])
const newChannelType = ref('')
const editingChannel = ref<ChannelConfig | null>(null)
const channelForm = ref({
  channel: '',
  config: {} as Record<string, string>,
  enabled: false,
})

const channelLabelMap: Record<string, string> = {
  wechat: '微信公众号',
  hugo: 'Hugo 博客',
  csdn: 'CSDN',
  zhihu: '知乎',
}

const allChannelTypes = [
  { value: 'wechat', label: '微信公众号' },
  { value: 'hugo', label: 'Hugo 博客' },
  { value: 'csdn', label: 'CSDN' },
  { value: 'zhihu', label: '知乎' },
]

const availableChannelTypes = computed(() => {
  const configured = new Set(channelConfigs.value.map((c) => c.channel))
  return allChannelTypes.filter((t) => !configured.has(t.value))
})

function isSecretMasked(val: string | undefined): boolean {
  return !!val && val.startsWith('••••')
}

// ── Email settings ──────────────────────────────────────────────────
const emailSettingsVisible = ref(false)
const emailFormRef = ref<FormInstance>()
const emailSaving = ref(false)
const emailTesting = ref(false)
const emailForm = ref<EmailSettings>({
  enabled: false,
  provider: 'smtp',
  from_email: '',
  from_name: '',
  reply_to: '',
  smtp: {
    host: '',
    port: 465,
    username: '',
    password: '',
    use_tls: true,
  },
})

const selectedEmailTemplate = ref('')

// Email service templates
const emailTemplates: Record<string, { host: string; port: number; desc: string }> = {
  feishu: { host: 'smtp.feishu.cn', port: 465, desc: '飞书邮箱' },
  qq: { host: 'smtp.qq.com', port: 465, desc: 'QQ邮箱' },
  '163': { host: 'smtp.163.com', port: 465, desc: '163邮箱' },
  gmail: { host: 'smtp.gmail.com', port: 587, desc: 'Gmail' },
  outlook: { host: 'smtp.office365.com', port: 587, desc: 'Outlook' },
}

function applyEmailTemplate() {
  const template = emailTemplates[selectedEmailTemplate.value]
  if (template) {
    emailForm.value.smtp.host = template.host
    emailForm.value.smtp.port = template.port
    emailForm.value.smtp.use_tls = template.port === 587
    ElMessage.success(`已应用${template.desc}配置模板`)
  }
}

function handlePortChange(port: number) {
  // Auto set use_tls based on port
  emailForm.value.smtp.use_tls = port === 587
}

function handleSecretFocus(field: string) {
  if (isSecretMasked(channelForm.value.config[field])) {
    channelForm.value.config[field] = ''
  }
}

function getDefaultConfig(channel: string): Record<string, string> {
  switch (channel) {
    case 'wechat':
      return { app_id: '', app_secret: '' }
    case 'hugo':
      return { repo_path: '', content_dir: 'content/posts' }
    default:
      return {}
  }
}

function showAddChannelForm() {
  if (!newChannelType.value) return
  editingChannel.value = null
  channelForm.value = {
    channel: newChannelType.value,
    config: getDefaultConfig(newChannelType.value),
    enabled: false,
  }
  channelFormVisible.value = true
}

function showEditChannelForm(cfg: ChannelConfig) {
  editingChannel.value = cfg
  channelForm.value = {
    channel: cfg.channel,
    config: { ...getDefaultConfig(cfg.channel), ...cfg.config },
    enabled: cfg.enabled,
  }
  channelFormVisible.value = true
}

async function loadChannels() {
  try {
    channelConfigs.value = await listChannels()
  } catch {
    ElMessage.error('加载渠道列表失败')
  }
}

async function handleSaveChannel() {
  // Build config, skip masked values
  const configToSend: Record<string, string> = {}
  for (const [k, v] of Object.entries(channelForm.value.config)) {
    if (!isSecretMasked(v)) {
      configToSend[k] = v
    }
  }

  try {
    if (editingChannel.value) {
      await updateChannel(editingChannel.value.id, {
        config: configToSend,
        enabled: channelForm.value.enabled,
      })
      ElMessage.success('渠道配置已更新')
    } else {
      await createChannel({
        channel: channelForm.value.channel,
        config: configToSend,
        enabled: channelForm.value.enabled,
      })
      ElMessage.success('渠道已添加')
      newChannelType.value = ''
    }
    channelFormVisible.value = false
    await loadChannels()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function handleToggleChannel(cfg: ChannelConfig, val: boolean) {
  try {
    await updateChannel(cfg.id, { enabled: val })
    cfg.enabled = val
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleDeleteChannel(channelId: number) {
  try {
    await deleteChannel(channelId)
    ElMessage.success('渠道已删除')
    await loadChannels()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ── Community CRUD ──────────────────────────────────────────────────
async function loadCommunities() {
  try {
    communities.value = await getCommunities()
  } catch {
    ElMessage.error('加载社区列表失败')
  }
}

function showCreateDialog() {
  isEditing.value = false
  editingId.value = null
  communityForm.value = { name: '', slug: '', description: '', url: '', logo_url: '' }
  dialogVisible.value = true
}

function showEditDialog(community: Community) {
  isEditing.value = true
  editingId.value = community.id
  communityForm.value = {
    name: community.name,
    slug: community.slug,
    description: community.description || '',
    url: community.url || '',
    logo_url: community.logo_url || '',
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEditing.value && editingId.value) {
      await updateCommunity(editingId.value, {
        name: communityForm.value.name,
        description: communityForm.value.description,
        url: communityForm.value.url || undefined,
        logo_url: communityForm.value.logo_url || undefined,
      })
      ElMessage.success('社区更新成功')
    } else {
      await createCommunity(communityForm.value)
      ElMessage.success('社区创建成功')
    }
    dialogVisible.value = false
    await loadCommunities()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleCommunityAction(command: string, community: Community) {
  switch (command) {
    case 'edit':
      showEditDialog(community)
      break
    case 'channels':
      selectedCommunity.value = community
      // Temporarily set current community for API calls
      localStorage.setItem('current_community_id', String(community.id))
      await loadChannels()
      channelsDialogVisible.value = true
      break
    case 'email':
      await showEmailSettingsDialog(community)
      break
    case 'members':
      await showMembersDialog(community)
      break
    case 'toggle':
      try {
        await updateCommunity(community.id, { is_active: !community.is_active })
        ElMessage.success(community.is_active ? '社区已停用' : '社区已启用')
        await loadCommunities()
      } catch {
        ElMessage.error('操作失败')
      }
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除社区 "${community.name}" 吗？此操作不可恢复，所有相关数据将被删除。`,
          '删除确认',
          { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
        )
        await deleteCommunity(community.id)
        ElMessage.success('社区已删除')
        await loadCommunities()
      } catch {
        // cancelled
      }
      break
  }
}

async function showMembersDialog(community: Community) {
  selectedCommunity.value = community
  selectedUserId.value = null
  try {
    communityUsers.value = await getCommunityUsers(community.id)
    allUsers.value = await listAllUsers()
  } catch {
    ElMessage.error('加载成员列表失败')
  }
  membersDialogVisible.value = true
}

async function handleAddMember() {
  if (!selectedCommunity.value || !selectedUserId.value) return
  try {
    await addUserToCommunity(selectedCommunity.value.id, selectedUserId.value)
    ElMessage.success('成员添加成功')
    communityUsers.value = await getCommunityUsers(selectedCommunity.value.id)
    selectedUserId.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '添加失败')
  }
}

async function handleRemoveMember(userId: number) {
  if (!selectedCommunity.value) return
  try {
    await removeUserFromCommunity(selectedCommunity.value.id, userId)
    ElMessage.success('成员已移除')
    communityUsers.value = await getCommunityUsers(selectedCommunity.value.id)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '移除失败')
  }
}

async function handleRoleChange(user: CommunityUser, newRole: string) {
  if (!selectedCommunity.value) return
  try {
    await updateUserRole(selectedCommunity.value.id, user.id, newRole)
    user.role = newRole
    ElMessage.success('角色更新成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新角色失败')
  }
}

// ── Email Settings ──────────────────────────────────────────────────
async function showEmailSettingsDialog(community: Community) {
  selectedCommunity.value = community
  selectedEmailTemplate.value = ''
  try {
    const settings = await getEmailSettings(community.id)
    emailForm.value = {
      enabled: settings.enabled,
      provider: settings.provider || 'smtp',
      from_email: settings.from_email || '',
      from_name: settings.from_name || '',
      reply_to: settings.reply_to || '',
      smtp: {
        host: settings.smtp?.host || '',
        port: settings.smtp?.port || 465,
        username: settings.smtp?.username || '',
        password: settings.smtp?.password || '',
        use_tls: settings.smtp?.use_tls !== undefined ? settings.smtp.use_tls : true,
      },
    }
  } catch (e: any) {
    ElMessage.error('加载邮件设置失败')
    // Set default values
    emailForm.value = {
      enabled: false,
      provider: 'smtp',
      from_email: '',
      from_name: '',
      reply_to: '',
      smtp: {
        host: '',
        port: 465,
        username: '',
        password: '',
        use_tls: true,
      },
    }
  }
  emailSettingsVisible.value = true
}

async function handleSaveEmailSettings() {
  if (!selectedCommunity.value) return
  
  // Validate password
  if (!emailForm.value.smtp.password) {
    ElMessage.warning('请填写SMTP密码')
    return
  }
  
  emailSaving.value = true
  try {
    const settingsToSave: EmailSettings = { ...emailForm.value }
    // Enable email settings when saving
    settingsToSave.enabled = true
    // If username is empty, use from_email
    if (!settingsToSave.smtp.username || !settingsToSave.smtp.username.trim()) {
      settingsToSave.smtp.username = settingsToSave.from_email
    }
    
    await updateEmailSettings(selectedCommunity.value.id, settingsToSave)
    ElMessage.success('邮件设置已保存')
    emailSettingsVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    emailSaving.value = false
  }
}

async function handleTestEmailSettings() {
  if (!selectedCommunity.value) return
  
  // Validate required fields
  if (!emailForm.value.from_email) {
    ElMessage.warning('请填写发件人邮箱')
    return
  }
  if (!emailForm.value.smtp.host) {
    ElMessage.warning('请填写SMTP服务器')
    return
  }
  // Check if password is configured
  if (!emailForm.value.smtp.password || emailForm.value.smtp.password.trim() === '') {
    ElMessage.warning('请填写SMTP密码')
    return
  }
  
  emailTesting.value = true
  try {
    // Save settings first (temporarily)
    const settingsToSave: EmailSettings = { ...emailForm.value }
    // Enable SMTP for testing
    settingsToSave.enabled = true
    // If username is empty, it will use from_email on backend
    if (!settingsToSave.smtp.username || !settingsToSave.smtp.username.trim()) {
      settingsToSave.smtp.username = settingsToSave.from_email
    }
    
    await updateEmailSettings(selectedCommunity.value.id, settingsToSave)
    
    // Test by sending to the from_email address
    const result = await testEmailSettings(
      selectedCommunity.value.id,
      emailForm.value.from_email
    )
    
    ElMessage.success(`测试邮件已发送到 ${emailForm.value.from_email}，请检查收件箱`)
  } catch (e: any) {
    ElMessage.error('测试失败：' + (e?.response?.data?.detail || e.message || '网络错误'))
  } finally {
    emailTesting.value = false
  }
}

onMounted(loadCommunities)
</script>

<style scoped>
.community-manage {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;

  padding: 32px 40px 60px;
  max-width: 1400px;
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

.community-card {
  margin-bottom: 20px;
  transition: all 0.2s ease;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.community-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.community-title .name {
  font-weight: 600;
  font-size: 18px;
  color: var(--text-primary);
}

.more-icon {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 18px;
  transition: color 0.15s ease;
}

.more-icon:hover {
  color: var(--blue);
}

.community-info .slug {
  color: var(--text-muted);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0 0 4px;
}

.community-info .url {
  font-size: 13px;
  margin: 0 0 8px;
}

.community-info .url a {
  color: var(--blue);
  text-decoration: none;
  transition: opacity 0.15s ease;
}

.community-info .url a:hover {
  text-decoration: underline;
  opacity: 0.85;
}

.community-info .desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
  line-height: 1.6;
}

.members-header,
.channels-header {
  display: flex;
  gap: 12px;
  align-items: center;
}

.hint-text {
  color: var(--text-muted);
  font-size: 13px;
}

.secret-hint {
  color: var(--text-muted);
  font-size: 12px;
  margin-top: 4px;
}

/* Element Plus overrides */
:deep(.el-card) {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

:deep(.el-card:hover) {
  box-shadow: var(--shadow-hover);
}

:deep(.el-card__header) {
  border-bottom: 1px solid #f1f5f9;
  padding: 18px 20px;
}

:deep(.el-card__body) {
  padding: 20px;
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

:deep(.el-dialog) {
  border-radius: var(--radius);
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #f1f5f9;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

:deep(.el-table) {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f8fafc;
}

:deep(.el-table th) {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
</style>
