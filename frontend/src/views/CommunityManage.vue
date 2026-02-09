<template>
  <div class="community-manage">
    <div class="page-header">
      <h2>社区管理</h2>
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
  type CommunityUser,
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
  await formRef.value.validate()

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
      await loadChannels()
      channelsDialogVisible.value = true
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

onMounted(loadCommunities)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; }

.community-card {
  margin-bottom: 20px;
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
  font-size: 16px;
}
.more-icon {
  cursor: pointer;
  color: #909399;
  font-size: 18px;
}
.more-icon:hover {
  color: #409eff;
}
.community-info .slug {
  color: #909399;
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
  color: #409eff;
  text-decoration: none;
}
.community-info .url a:hover {
  text-decoration: underline;
}
.community-info .desc {
  color: #606266;
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

.hint-text { color: #999; font-size: 13px; }
.secret-hint { color: #909399; font-size: 12px; margin-top: 4px; }
</style>
