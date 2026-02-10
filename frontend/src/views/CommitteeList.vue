<template>
  <div class="committee-list">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-header">
        <div class="header-title">
          <h2>委员会管理</h2>
          <p>管理社区的各类委员会及其成员</p>
        </div>
        <el-button
          v-if="isAdmin"
          type="primary"
          @click="showCreateDialog = true"
        >
          <el-icon><Plus /></el-icon>
          创建委员会
        </el-button>
      </div>

      <div class="filter-bar">
        <el-radio-group v-model="filterActive" @change="loadCommittees">
          <el-radio-button :value="undefined">全部</el-radio-button>
          <el-radio-button :value="true">活跃</el-radio-button>
          <el-radio-button :value="false">已归档</el-radio-button>
        </el-radio-group>
      </div>

      <el-row v-loading="loading" :gutter="16" class="committee-grid">
        <el-col
          v-for="committee in committees"
          :key="committee.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <el-card class="committee-card" shadow="hover" @click="goToDetail(committee.id)">
            <div class="card-header">
              <h3>{{ committee.name }}</h3>
              <el-tag :type="committee.is_active ? 'success' : 'info'" size="small">
                {{ committee.is_active ? '活跃' : '已归档' }}
              </el-tag>
            </div>

            <div v-if="committee.description" class="card-description">
              {{ committee.description }}
            </div>

            <div class="card-meta">
              <div class="meta-item">
                <el-icon><UserFilled /></el-icon>
                <span>{{ committee.member_count }} 名成员</span>
              </div>
            </div>

            <div v-if="isAdmin" class="card-actions" @click.stop>
              <el-button
                type="primary"
                size="small"
                link
                @click="editCommittee(committee)"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                link
                @click="confirmDelete(committee)"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="!loading && committees.length === 0" description="暂无委员会" />

      <!-- Create/Edit Dialog -->
      <el-dialog
        v-model="showCreateDialog"
        :title="editingCommittee ? '编辑委员会' : '创建委员会'"
        width="600px"
      >
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="120px"
        >
          <el-form-item label="委员会名称" prop="name">
            <el-input v-model="form.name" placeholder="如：技术委员会" />
          </el-form-item>

          <el-form-item label="标识符" prop="slug">
            <el-input
              v-model="form.slug"
              placeholder="如：technical-committee"
              :disabled="!!editingCommittee"
            >
              <template #append>.committee</template>
            </el-input>
            <div class="form-tip">仅可包含小写字母、数字和连字符，创建后不可修改</div>
          </el-form-item>

          <el-form-item label="委员会简介" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="简要描述委员会的职责和目标"
            />
          </el-form-item>

          <el-form-item label="通知邮箱" prop="notification_email">
            <el-input
              v-model="form.notification_email"
              placeholder="用于发送通知的邮箱"
            />
          </el-form-item>

          <el-form-item label="微信通知" prop="notification_wechat">
            <el-input
              v-model="form.notification_wechat"
              placeholder="企业微信群ID或其他标识"
            />
          </el-form-item>

          <el-form-item v-if="editingCommittee" label="状态" prop="is_active">
            <el-switch
              v-model="form.is_active"
              active-text="活跃"
              inactive-text="已归档"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            {{ editingCommittee ? '更新' : '创建' }}
          </el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, UserFilled, Edit, Delete } from '@element-plus/icons-vue'
import {
  listCommittees,
  createCommittee,
  updateCommittee,
  deleteCommittee,
  type Committee,
  type CommitteeCreate,
  type CommitteeUpdate
} from '@/api/governance'
import { useUserStore } from '@/stores/user'
import { useCommunityStore } from '@/stores/community'

const router = useRouter()
const userStore = useUserStore()
const communityStore = useCommunityStore()

const isAdmin = computed(() => userStore.isCommunityAdmin)

const loading = ref(false)
const submitting = ref(false)
const committees = ref<Committee[]>([])
const filterActive = ref<boolean | undefined>(undefined)

const showCreateDialog = ref(false)
const editingCommittee = ref<Committee | null>(null)
const formRef = ref<FormInstance>()

interface CommitteeForm {
  name: string
  slug: string
  description?: string
  notification_email?: string
  notification_wechat?: string
  is_active?: boolean
}

const form = ref<CommitteeForm>({
  name: '',
  slug: '',
  description: '',
  notification_email: '',
  notification_wechat: '',
  is_active: true
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入委员会名称', trigger: 'blur' },
    { min: 1, max: 200, message: '名称长度在1-200个字符', trigger: 'blur' }
  ],
  slug: [
    { required: true, message: '请输入标识符', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '仅可包含小写字母、数字和连字符', trigger: 'blur' }
  ]
}

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadCommittees()
  }
})

// Watch for community changes
watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) {
      loadCommittees()
    }
  }
)

async function loadCommittees() {
  loading.value = true
  try {
    const params = filterActive.value !== undefined ? { is_active: filterActive.value } : {}
    committees.value = await listCommittees(params)
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会列表失败')
  } finally {
    loading.value = false
  }
}

function goToDetail(id: number) {
  router.push(`/committees/${id}`)
}

function editCommittee(committee: Committee) {
  editingCommittee.value = committee
  form.value = {
    name: committee.name,
    slug: committee.slug,
    description: committee.description,
    notification_email: committee.notification_email,
    notification_wechat: committee.notification_wechat,
    is_active: committee.is_active
  }
  showCreateDialog.value = true
}

async function confirmDelete(committee: Committee) {
  try {
    await ElMessageBox.confirm(
      `确定要删除委员会"${committee.name}"吗？这将同时删除所有成员和会议记录。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    await deleteCommittee(committee.id)
    ElMessage.success('删除成功')
    loadCommittees()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function submitForm() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (editingCommittee.value) {
        const updateData: CommitteeUpdate = {
          name: form.value.name,
          description: form.value.description,
          notification_email: form.value.notification_email,
          notification_wechat: form.value.notification_wechat,
          is_active: form.value.is_active
        }
        await updateCommittee(editingCommittee.value.id, updateData)
        ElMessage.success('更新成功')
      } else {
        const createData: CommitteeCreate = {
          name: form.value.name,
          slug: form.value.slug,
          description: form.value.description,
          notification_email: form.value.notification_email,
          notification_wechat: form.value.notification_wechat
        }
        await createCommittee(createData)
        ElMessage.success('创建成功')
      }
      showCreateDialog.value = false
      editingCommittee.value = null
      formRef.value?.resetFields()
      loadCommittees()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

</script>

<style scoped>
.committee-list {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-title h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
}

.header-title p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.filter-bar {
  margin-bottom: 24px;
}

.committee-grid {
  margin-bottom: 24px;
}

.committee-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.committee-card:hover {
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  flex: 1;
}

.card-description {
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.meta-item .el-icon {
  font-size: 14px;
}

.card-actions {
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
