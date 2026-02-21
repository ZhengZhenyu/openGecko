<template>
  <div class="content-edit">
    <div class="page-header">
      <h2>{{ isNew ? '新建内容' : '编辑内容' }}</h2>
      <div class="actions">
        <el-button @click="$router.back()">返回</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
        <el-button v-if="!isNew" type="success" @click="$router.push(`/publish/${contentId}`)">去发布</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="meta-card">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="标题">
                <el-input v-model="form.title" placeholder="请输入文章标题" />
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="来源">
                <el-select v-model="form.source_type" style="width: 100%">
                  <el-option label="社区投稿" value="contribution" />
                  <el-option label="Release Note" value="release_note" />
                  <el-option label="活动总结" value="event_summary" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="作者">
                <el-input v-model="form.author" placeholder="作者" />
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="分类">
                <el-input v-model="form.category" placeholder="分类" />
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="标签">
                <el-input v-model="tagsInput" placeholder="逗号分隔" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- Work Status and Assignees -->
          <el-row :gutter="16" style="margin-top: 12px">
            <el-col :span="4">
              <el-form-item label="工作状态">
                <el-select v-model="form.work_status" style="width: 100%">
                  <el-option label="计划中" value="planning" />
                  <el-option label="实施中" value="in_progress" />
                  <el-option label="已完成" value="completed" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="20">
              <el-form-item label="责任人">
                <el-select
                  v-model="assigneeIds"
                  multiple
                  filterable
                  placeholder="选择责任人（默认为创建者）"
                  style="width: 100%"
                >
                  <el-option
                    v-for="u in communityMembers"
                    :key="u.id"
                    :label="`${u.username} (${u.email})`"
                    :value="u.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- Cover Image Upload -->
          <el-row :gutter="16" style="margin-top: 12px">
            <el-col :span="24">
              <el-form-item label="封面图（微信发布必需）">
                <div class="cover-upload-area">
                  <div v-if="coverImageUrl" class="cover-preview">
                    <img :src="coverImageUrl" alt="封面图" />
                    <div class="cover-actions">
                      <el-button size="small" type="danger" @click="removeCover">移除</el-button>
                      <el-button size="small" type="primary" @click="triggerCoverUpload">更换</el-button>
                    </div>
                  </div>
                  <div v-else class="cover-placeholder" @click="triggerCoverUpload">
                    <el-icon :size="32"><Plus /></el-icon>
                    <span>点击上传封面图</span>
                    <span class="hint">支持 JPG/PNG/GIF/WebP，建议比例 2.35:1，不超过 10MB</span>
                  </div>
                  <input
                    ref="coverInput"
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    style="display: none"
                    @change="handleCoverSelect"
                  />
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>
        <div class="editor-header">
          <span class="editor-title">正文内容</span>
          <div class="editor-mode-toggle">
            <button
              class="mode-btn"
              :class="{ active: editorMode === 'markdown' }"
              @click="editorMode = 'markdown'"
            >Markdown</button>
            <button
              class="mode-btn"
              :class="{ active: editorMode === 'html' }"
              @click="editorMode = 'html'"
            >HTML（135 等富文本）</button>
          </div>
        </div>
        <p v-if="editorMode === 'html'" class="editor-mode-hint">
          粘贴从 135 编辑器、飞书、公众号等复制的 HTML 源码，发布微信时将直接使用，无需转换。
        </p>
      </template>
      <MdEditorV3
        v-if="editorMode === 'markdown'"
        v-model="form.content_markdown"
        :preview="true"
        language="zh-CN"
        style="height: 600px"
      />
      <textarea
        v-else
        v-model="form.content_html"
        class="html-editor"
        placeholder="在此粘贴 HTML 源码..."
        spellcheck="false"
      />
    </el-card>

    <!-- Collaborator Management (only for existing content) -->
    <el-card v-if="!isNew" style="margin-top: 16px">
      <template #header>
        <div class="collab-header">
          <span>协作者管理</span>
          <el-tag v-if="isOwner" type="success" size="small">你是所有者</el-tag>
        </div>
      </template>
      <div class="collab-section">
        <div class="collab-add" v-if="isOwner || isSuperuser">
          <el-select
            v-model="selectedCollaboratorId"
            filterable
            placeholder="搜索用户添加协作者"
            style="width: 280px"
          >
            <el-option
              v-for="u in availableCommunityUsers"
              :key="u.id"
              :label="`${u.username} (${u.email})`"
              :value="u.id"
            />
          </el-select>
          <el-button type="primary" :disabled="!selectedCollaboratorId" @click="handleAddCollaborator">
            添加协作者
          </el-button>
        </div>
        <div v-if="collaborators.length > 0" class="collab-list">
          <el-tag
            v-for="collab in collaborators"
            :key="collab.id"
            :closable="isOwner || isSuperuser"
            size="default"
            style="margin: 4px"
            @close="handleRemoveCollaborator(collab.id)"
          >
            {{ collab.username }}
          </el-tag>
        </div>
        <div v-else class="collab-empty">暂无协作者</div>

        <!-- Ownership transfer -->
        <div v-if="isOwner || isSuperuser" class="ownership-section">
          <el-divider />
          <div class="ownership-transfer">
            <span class="label">转让所有权：</span>
            <el-select
              v-model="newOwnerId"
              filterable
              placeholder="选择新所有者"
              style="width: 240px"
            >
              <el-option
                v-for="u in availableCommunityUsers"
                :key="u.id"
                :label="`${u.username} (${u.email})`"
                :value="u.id"
              />
            </el-select>
            <el-popconfirm title="确定转让所有权？" @confirm="handleTransferOwnership">
              <template #reference>
                <el-button type="warning" :disabled="!newOwnerId" size="small">确认转让</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { MdEditor as MdEditorV3 } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import {
  fetchContent,
  createContent,
  updateContent,
  uploadCoverImage,
  listCollaborators,
  addCollaborator,
  removeCollaborator,
  transferOwnership,
} from '../api/content'
import { getCommunityUsers, type CommunityUser } from '../api/community'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'

const route = useRoute()
const router = useRouter()
const saving = ref(false)
const coverInput = ref<HTMLInputElement | null>(null)
const coverImageUrl = ref<string | null>(null)
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const contentId = computed(() => route.params.id ? Number(route.params.id) : null)
const isNew = computed(() => !contentId.value)
const isSuperuser = computed(() => authStore.isSuperuser)

const contentOwnerId = ref<number | null>(null)
const isOwner = computed(() => contentOwnerId.value === authStore.user?.id)

// Collaborator state
const collaborators = ref<{ id: number; username: string; email: string }[]>([])
const communityMembers = ref<CommunityUser[]>([])
const selectedCollaboratorId = ref<number | null>(null)
const newOwnerId = ref<number | null>(null)

const availableCommunityUsers = computed(() => {
  const collabIds = new Set(collaborators.value.map((c) => c.id))
  const currentUserId = authStore.user?.id
  return communityMembers.value.filter(
    (u) => !collabIds.has(u.id) && u.id !== currentUserId && u.id !== contentOwnerId.value
  )
})

const form = ref({
  title: '',
  content_markdown: '',
  content_html: '',
  source_type: 'contribution',
  author: '',
  category: '',
  tags: [] as string[],
  work_status: 'planning',
})
const tagsInput = ref('')
const assigneeIds = ref<number[]>([])
// 编辑器模式：markdown（默认）或 html（135 等富文本粘贴）
const editorMode = ref<'markdown' | 'html'>('markdown')

onMounted(async () => {
  // Load community members first
  const communityId = communityStore.currentCommunityId
  if (communityId) {
    try {
      communityMembers.value = await getCommunityUsers(communityId)
    } catch {
      // ignore
    }
  }

  if (contentId.value) {
    const data = await fetchContent(contentId.value)
    form.value = {
      title: data.title,
      content_markdown: data.content_markdown,
      content_html: data.content_html,
      source_type: data.source_type,
      author: data.author,
      category: data.category,
      tags: data.tags,
      work_status: data.work_status || 'planning',
    }
    // 如果已有 HTML 内容则自动切换到 HTML 模式
    if (data.content_html && data.content_html.trim()) {
      editorMode.value = 'html'
    }
    tagsInput.value = data.tags.join(', ')
    coverImageUrl.value = data.cover_image || null
    contentOwnerId.value = data.owner_id
    assigneeIds.value = data.assignee_ids || []

    // Load collaborators
    try {
      collaborators.value = await listCollaborators(contentId.value)
    } catch {
      // ignore
    }
  } else {
    // For new content, default assignee to current user
    if (authStore.user?.id) {
      assigneeIds.value = [authStore.user.id]
    }
  }
})

function triggerCoverUpload() {
  coverInput.value?.click()
}

async function handleCoverSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (!contentId.value) {
    ElMessage.warning('请先保存内容后再上传封面图')
    input.value = ''
    return
  }

  try {
    const updated = await uploadCoverImage(contentId.value, file)
    coverImageUrl.value = updated.cover_image
    ElMessage.success('封面图上传成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '封面图上传失败')
  }
  input.value = ''
}

async function removeCover() {
  if (!contentId.value) return
  try {
    await updateContent(contentId.value, { cover_image: '' } as any)
    coverImageUrl.value = null
    ElMessage.success('封面图已移除')
  } catch (e: any) {
    ElMessage.error('移除封面图失败')
  }
}

async function handleSave() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  saving.value = true
  try {
    const payload = {
      ...form.value,
      tags: tagsInput.value.split(/[,，]/).map(t => t.trim()).filter(Boolean),
      assignee_ids: assigneeIds.value,
      // HTML 模式下清空 markdown，避免发布时走 markdown 转换路径
      content_markdown: editorMode.value === 'html' ? '' : form.value.content_markdown,
      content_html: editorMode.value === 'markdown' ? '' : form.value.content_html,
    }
    if (isNew.value) {
      const created = await createContent(payload)
      ElMessage.success('创建成功')
      router.replace(`/contents/${created.id}/edit`)
    } else {
      await updateContent(contentId.value!, payload)
      ElMessage.success('保存成功')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// Collaborator management handlers

async function handleAddCollaborator() {
  if (!contentId.value || !selectedCollaboratorId.value) return
  try {
    await addCollaborator(contentId.value, selectedCollaboratorId.value)
    ElMessage.success('协作者添加成功')
    collaborators.value = await listCollaborators(contentId.value)
    selectedCollaboratorId.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '添加协作者失败')
  }
}

async function handleRemoveCollaborator(userId: number) {
  if (!contentId.value) return
  try {
    await removeCollaborator(contentId.value, userId)
    ElMessage.success('协作者已移除')
    collaborators.value = await listCollaborators(contentId.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '移除协作者失败')
  }
}

async function handleTransferOwnership() {
  if (!contentId.value || !newOwnerId.value) return
  try {
    await transferOwnership(contentId.value, newOwnerId.value)
    ElMessage.success('所有权已转让')
    contentOwnerId.value = newOwnerId.value
    newOwnerId.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '转让所有权失败')
  }
}
</script>

<style scoped>
/* LFX Insights Light Theme - Content Edit */
.content-edit {
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

.actions {
  display: flex;
  gap: 10px;
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
  margin-bottom: 24px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Form Overrides */
.meta-card :deep(.el-form-item) {
  margin-bottom: 0;
}

.meta-card :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-weight: 500;
}

.meta-card :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}

.meta-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}

.meta-card :deep(.el-input__inner) {
  color: var(--text-primary);
}

.meta-card :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

/* Collaborators */
.collab-add {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.collab-list {
  padding: 12px 0;
}

.collab-empty {
  color: var(--text-muted);
  font-size: 14px;
  padding: 12px 0;
  text-align: center;
}

.ownership-section .label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-right: 12px;
  font-weight: 500;
}

.ownership-transfer {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Cover Upload */
.cover-upload-area {
  width: 320px;
}

.cover-preview {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: #f8fafc;
  transition: all 0.2s ease;
}

.cover-preview:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-hover);
}

.cover-preview img {
  width: 100%;
  height: 136px;
  object-fit: cover;
  display: block;
}

.cover-actions {
  display: flex;
  gap: 8px;
  padding: 10px;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-top: 1px solid #f1f5f9;
}

.cover-placeholder {
  width: 100%;
  height: 136px;
  border: 2px dashed var(--border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  gap: 6px;
  transition: all 0.2s ease;
  background: #f8fafc;
}

.cover-placeholder:hover {
  border-color: var(--blue);
  color: var(--blue);
  background: #eff6ff;
}

.cover-placeholder span {
  font-size: 14px;
  font-weight: 500;
}

.cover-placeholder .hint {
  font-size: 12px;
  color: var(--text-muted);
}

/* Element Plus Overrides */
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

:deep(.el-button--success) {
  background: #22c55e;
  border-color: #22c55e;
}

:deep(.el-button--success:hover) {
  background: #16a34a;
  border-color: #16a34a;
}

:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

:deep(.el-button--default:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

/* 编辑器模式切换 */
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.editor-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.editor-mode-toggle {
  display: flex;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  padding: 4px 14px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-btn.active {
  background: #ffffff;
  color: #0095ff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.mode-btn:hover:not(.active) {
  color: #1e293b;
}

.editor-mode-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.5;
}

.html-editor {
  display: block;
  width: 100%;
  height: 600px;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #334155;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  tab-size: 2;
}

.html-editor:focus {
  border-color: #0095ff;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(0, 149, 255, 0.08);
}
</style>
