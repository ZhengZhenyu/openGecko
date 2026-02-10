<template>
  <div v-loading="loading" class="committee-detail">
    <div v-if="committee" class="detail-container">
      <!-- Committee Header -->
      <div class="detail-header">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>

      <el-card class="committee-info-card">
        <div class="committee-header">
          <div class="committee-title">
            <h2>{{ committee.name }}</h2>
            <el-tag :type="committee.is_active ? 'success' : 'info'">
              {{ committee.is_active ? '活跃' : '已归档' }}
            </el-tag>
          </div>
          <el-button
            v-if="isAdmin"
            type="primary"
            @click="editCommittee"
          >
            <el-icon><Edit /></el-icon>
            编辑委员会
          </el-button>
        </div>

        <div v-if="committee.description" class="committee-description">
          {{ committee.description }}
        </div>

        <el-row :gutter="16" class="committee-meta">
          <el-col :span="12">
            <div class="meta-card">
              <el-icon><UserFilled /></el-icon>
              <div class="meta-content">
                <div class="meta-label">成员数量</div>
                <div class="meta-value">{{ committee.member_count }} 人</div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="meta-card">
              <el-icon><Calendar /></el-icon>
              <div class="meta-content">
                <div class="meta-label">会议频率</div>
                <div class="meta-value">{{ committee.meeting_frequency || '未设置' }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- Members Section -->
      <div class="members-section">
        <div class="section-header">
          <h3>委员会成员</h3>
          <el-button
            v-if="isAdmin"
            type="primary"
            @click="showMemberDialog = true"
          >
            <el-icon><Plus /></el-icon>
            添加成员
          </el-button>
        </div>

        <div class="members-filter">
          <el-radio-group v-model="memberFilter" @change="filterMembers">
            <el-radio-button :value="undefined">全部成员</el-radio-button>
            <el-radio-button :value="true">在任</el-radio-button>
            <el-radio-button :value="false">已离任</el-radio-button>
          </el-radio-group>
        </div>

        <el-row :gutter="16">
          <el-col
            v-for="member in filteredMembers"
            :key="member.id"
            :xs="24"
            :sm="12"
            :md="8"
          >
            <MemberCard
              :member="member"
              :show-actions="isAdmin"
              @edit="editMember"
              @delete="confirmDeleteMember"
            />
          </el-col>
        </el-row>

        <el-empty
          v-if="filteredMembers.length === 0"
          description="暂无成员"
        />
      </div>
    </div>

    <!-- Member Dialog -->
    <el-dialog
      v-model="showMemberDialog"
      :title="editingMember ? '编辑成员' : '添加成员'"
      width="600px"
    >
      <el-form
        ref="memberFormRef"
        :model="memberForm"
        :rules="memberRules"
        label-width="100px"
      >
        <el-form-item label="姓名" prop="name">
          <el-input v-model="memberForm.name" placeholder="成员姓名" />
        </el-form-item>

        <el-form-item label="组织" prop="organization">
          <el-input v-model="memberForm.organization" placeholder="所属组织或公司" />
        </el-form-item>

        <el-form-item label="角色" prop="roles">
          <el-select
            v-model="memberForm.roles"
            multiple
            placeholder="选择角色"
            style="width: 100%"
          >
            <el-option label="主席" value="chair" />
            <el-option label="副主席" value="vice_chair" />
            <el-option label="秘书长" value="secretary" />
            <el-option label="委员" value="member" />
            <el-option label="观察员" value="observer" />
          </el-select>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="memberForm.email" placeholder="email@example.com" />
        </el-form-item>

        <el-form-item label="电话" prop="phone">
          <el-input v-model="memberForm.phone" placeholder="联系电话" />
        </el-form-item>

        <el-form-item label="微信" prop="wechat">
          <el-input v-model="memberForm.wechat" placeholder="微信号" />
        </el-form-item>

        <el-form-item label="任期开始" prop="term_start">
          <el-date-picker
            v-model="memberForm.term_start"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="任期结束" prop="term_end">
          <el-date-picker
            v-model="memberForm.term_end"
            type="date"
            placeholder="选择结束日期（可选）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="个人简介" prop="bio">
          <el-input
            v-model="memberForm.bio"
            type="textarea"
            :rows="3"
            placeholder="简要介绍成员背景"
          />
        </el-form-item>

        <el-form-item v-if="editingMember" label="状态" prop="is_active">
          <el-switch
            v-model="memberForm.is_active"
            active-text="在任"
            inactive-text="已离任"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showMemberDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMemberForm">
          {{ editingMember ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  UserFilled,
  Calendar,
  Clock,
  Plus
} from '@element-plus/icons-vue'
import {
  getCommittee,
  createCommitteeMember,
  updateCommitteeMember,
  deleteCommitteeMember,
  type CommitteeWithMembers,
  type CommitteeMember,
  type CommitteeMemberCreate,
  type CommitteeMemberUpdate
} from '@/api/governance'
import MemberCard from '@/components/MemberCard.vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.isCommunityAdmin)

const loading = ref(false)
const submitting = ref(false)
const committee = ref<CommitteeWithMembers | null>(null)
const memberFilter = ref<boolean | undefined>(undefined)

const showMemberDialog = ref(false)
const editingMember = ref<CommitteeMember | null>(null)
const memberFormRef = ref<FormInstance>()

interface MemberForm {
  name: string
  organization?: string
  roles: string[]
  email?: string
  phone?: string
  wechat?: string
  term_start?: string
  term_end?: string
  bio?: string
  is_active?: boolean
}

const memberForm = ref<MemberForm>({
  name: '',
  organization: '',
  roles: [],
  email: '',
  phone: '',
  wechat: '',
  term_start: '',
  term_end: '',
  bio: '',
  is_active: true
})

const memberRules: FormRules = {
  name: [
    { required: true, message: '请输入成员姓名', trigger: 'blur' },
    { min: 1, max: 200, message: '姓名长度在1-200个字符', trigger: 'blur' }
  ]
}

const filteredMembers = computed(() => {
  if (!committee.value?.members) return []
  if (memberFilter.value === undefined) return committee.value.members
  return committee.value.members.filter(m => m.is_active === memberFilter.value)
})

onMounted(() => {
  loadCommittee()
})

async function loadCommittee() {
  const id = parseInt(route.params.id as string)
  if (isNaN(id)) return

  loading.value = true
  try {
    committee.value = await getCommittee(id)
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会详情失败')
  } finally {
    loading.value = false
  }
}

function editCommittee() {
  // TODO: Navigate to committee edit page or show edit dialog
  ElMessage.info('编辑委员会功能待实现（可在列表页编辑）')
}

function editMember(member: CommitteeMember) {
  editingMember.value = member
  memberForm.value = {
    name: member.name,
    organization: member.organization,
    roles: member.roles || [],
    email: member.email,
    phone: member.phone,
    wechat: member.wechat,
    term_start: member.term_start,
    term_end: member.term_end,
    bio: member.bio,
    is_active: member.is_active
  }
  showMemberDialog.value = true
}

async function confirmDeleteMember(member: CommitteeMember) {
  if (!committee.value) return

  try {
    await ElMessageBox.confirm(
      `确定要删除成员"${member.name}"吗？`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    await deleteCommitteeMember(committee.value.id, member.id)
    ElMessage.success('删除成功')
    loadCommittee()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function submitMemberForm() {
  if (!memberFormRef.value || !committee.value) return

  await memberFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (editingMember.value) {
        const updateData: CommitteeMemberUpdate = {
          name: memberForm.value.name,
          organization: memberForm.value.organization,
          roles: memberForm.value.roles,
          email: memberForm.value.email,
          phone: memberForm.value.phone,
          wechat: memberForm.value.wechat,
          term_start: memberForm.value.term_start,
          term_end: memberForm.value.term_end,
          bio: memberForm.value.bio,
          is_active: memberForm.value.is_active
        }
        await updateCommitteeMember(committee.value.id, editingMember.value.id, updateData)
        ElMessage.success('更新成功')
      } else {
        const createData: CommitteeMemberCreate = {
          name: memberForm.value.name,
          organization: memberForm.value.organization,
          roles: memberForm.value.roles,
          email: memberForm.value.email,
          phone: memberForm.value.phone,
          wechat: memberForm.value.wechat,
          term_start: memberForm.value.term_start,
          term_end: memberForm.value.term_end,
          bio: memberForm.value.bio
        }
        await createCommitteeMember(committee.value.id, createData)
        ElMessage.success('添加成功')
      }
      showMemberDialog.value = false
      editingMember.value = null
      memberFormRef.value?.resetFields()
      loadCommittee()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

function filterMembers() {
  // Computed property will auto-update
}

function formatDate(dateStr?: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.committee-detail {
  padding: 24px;
}

.detail-header {
  margin-bottom: 16px;
}

.committee-info-card {
  margin-bottom: 24px;
}

.committee-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.committee-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.committee-title h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.committee-description {
  color: var(--el-text-color-regular);
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.committee-meta {
  margin-top: 24px;
}

.meta-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.meta-card .el-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.meta-content {
  flex: 1;
}

.meta-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.meta-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.members-section {
  margin-top: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.members-filter {
  margin-bottom: 16px;
}
</style>
