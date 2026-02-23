<template>
  <div class="content-edit">
    <!-- 顶部粘性操作栏 -->
    <div class="top-bar">
      <button class="back-btn" @click="$router.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        返回
      </button>
      <span class="top-bar-title">{{ isNew ? '新建内容' : '编辑内容' }}</span>
      <div class="top-bar-actions">
        <el-button v-if="!isNew" type="success" size="small" @click="$router.push(`/publish/${contentId}`)">
          去发布
        </el-button>
        <el-button type="primary" size="small" @click="handleSave" :loading="saving">保存</el-button>
      </div>
    </div>

    <!-- 主体区域：左侧编辑 + 右侧元数据 -->
    <div class="edit-body">
      <!-- 左：标题 + 正文 -->
      <div class="edit-main">
        <input
          v-model="form.title"
          class="title-input"
          placeholder="请输入文章标题…"
          maxlength="200"
        />

        <!-- 编辑器卡片 -->
        <div class="editor-card">
          <div class="editor-card-header">
            <div class="editor-mode-toggle">
              <button class="mode-btn" :class="{ active: editorMode === 'markdown' }" @click="editorMode = 'markdown'">Markdown</button>
              <button class="mode-btn" :class="{ active: editorMode === 'html' }" @click="editorMode = 'html'">HTML（135 等富文本）</button>
            </div>
            <span v-if="editorMode === 'html'" class="editor-hint">粘贴 135/飞书 等的 HTML 源码，发布微信时直接使用</span>
          </div>
          <MdEditorV3
            v-if="editorMode === 'markdown'"
            v-model="form.content_markdown"
            :preview="true"
            language="zh-CN"
            style="height: 620px; border-radius: 0 0 12px 12px; border: none;"
          />
          <textarea
            v-else
            v-model="form.content_html"
            class="html-editor"
            placeholder="在此粘贴 HTML 源码…"
            spellcheck="false"
          />
        </div>

        <!-- 协作者管理（仅已保存内容） -->
        <div v-if="!isNew" class="collab-card">
          <div class="collab-card-header">
            <span class="card-title">协作者</span>
            <el-tag v-if="isOwner" type="success" size="small">你是所有者</el-tag>
          </div>
          <div v-if="isOwner || isSuperuser" class="collab-add">
            <el-select v-model="selectedCollaboratorId" filterable placeholder="搜索成员并添加" style="flex: 1">
              <el-option v-for="u in availableCommunityUsers" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
            </el-select>
            <el-button type="primary" :disabled="!selectedCollaboratorId" @click="handleAddCollaborator">添加</el-button>
          </div>
          <div v-if="collaborators.length > 0" class="collab-tags">
            <el-tag v-for="collab in collaborators" :key="collab.id" :closable="isOwner || isSuperuser" style="margin: 3px" @close="handleRemoveCollaborator(collab.id)">
              {{ collab.username }}
            </el-tag>
          </div>
          <p v-else class="collab-empty">暂无协作者</p>
          <div v-if="isOwner || isSuperuser" class="transfer-row">
            <el-divider style="margin: 12px 0" />
            <span class="field-label">转让所有权</span>
            <div class="transfer-controls">
              <el-select v-model="newOwnerId" filterable placeholder="选择新所有者" style="flex: 1">
                <el-option v-for="u in availableCommunityUsers" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
              </el-select>
              <el-popconfirm title="确定转让所有权？" @confirm="handleTransferOwnership">
                <template #reference>
                  <el-button type="warning" :disabled="!newOwnerId" size="small">确认转让</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
      </div>

      <!-- 右：元数据面板 -->
      <div class="meta-panel">
        <!-- 封面图 -->
        <div class="meta-section">
          <div class="meta-section-title">封面图</div>
          <div class="cover-upload" @click="triggerCoverUpload">
            <img v-if="coverImageUrl" :src="coverImageUrl" class="cover-preview-img" alt="封面图" />
            <div v-else class="cover-placeholder">
              <el-icon :size="24"><Plus /></el-icon>
              <span>点击上传</span>
              <span class="cover-hint">建议比例 2.35:1</span>
            </div>
          </div>
          <div v-if="coverImageUrl" class="cover-actions-row">
            <button class="cover-action-btn" @click="triggerCoverUpload">更换</button>
            <button class="cover-action-btn danger" @click="removeCover">移除</button>
          </div>
          <input ref="coverInput" type="file" accept="image/jpeg,image/png,image/gif,image/webp" style="display:none" @change="handleCoverSelect" />
        </div>

        <!-- 基本信息 -->
        <div class="meta-section">
          <div class="meta-section-title">基本信息</div>
          <div class="field-group">
            <label class="field-label">来源类型</label>
            <el-select v-model="form.source_type" size="small" style="width:100%">
              <el-option label="社区投稿" value="contribution" />
              <el-option label="Release Note" value="release_note" />
              <el-option label="活动总结" value="event_summary" />
            </el-select>
          </div>
          <div class="field-group">
            <label class="field-label">作者</label>
            <el-input v-model="form.author" placeholder="作者姓名" size="small" />
          </div>
          <div class="field-group">
            <label class="field-label">分类</label>
            <el-input v-model="form.category" placeholder="文章分类" size="small" />
          </div>
          <div class="field-group">
            <label class="field-label">标签</label>
            <el-input v-model="tagsInput" placeholder="逗号分隔，如：技术,社区" size="small" />
          </div>
        </div>

        <!-- 工作流 -->
        <div class="meta-section">
          <div class="meta-section-title">工作流</div>
          <div class="field-group">
            <label class="field-label">工作状态</label>
            <el-select v-model="form.work_status" size="small" style="width:100%">
              <el-option label="计划中" value="planning" />
              <el-option label="实施中" value="in_progress" />
              <el-option label="已完成" value="completed" />
            </el-select>
          </div>
          <div class="field-group">
            <label class="field-label">责任人</label>
            <el-select v-model="assigneeIds" multiple filterable placeholder="选择责任人" size="small" style="width:100%">
              <el-option v-for="u in communityMembers" :key="u.id" :label="`${u.username}`" :value="u.id" />
            </el-select>
          </div>
        </div>

        <!-- 关联社区 -->
        <div class="meta-section">
          <div class="meta-section-title">关联社区</div>
          <el-select
            v-model="communityIds"
            multiple
            placeholder="选择关联社区（可多选）"
            size="small"
            style="width:100%"
          >
            <el-option
              v-for="c in authStore.communities"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
          <p class="community-hint">内容可关联多个社区，或不关联任何社区</p>
        </div>
      </div>
    </div>
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
const communityIds = ref<number[]>([])
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
    communityIds.value = data.community_ids?.length ? data.community_ids : (data.community_id ? [data.community_id] : [])

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
    // For new content, pre-fill community with current community
    if (communityStore.currentCommunityId) {
      communityIds.value = [communityStore.currentCommunityId]
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
      community_ids: communityIds.value,
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
.content-edit {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --border: #e2e8f0;
  --bg: #f5f7fa;
  --card-bg: #ffffff;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --radius: 12px;
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  flex-direction: column;
}

/* ── 顶部操作栏 ── */
.top-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 32px;
  height: 52px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 7px;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}
.back-btn:hover { background: #f1f5f9; color: var(--text-primary); }

.top-bar-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-bar-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* ── 主体双栏 ── */
.edit-body {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
  padding: 24px 32px 60px;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* ── 左侧 ── */
.edit-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.title-input {
  width: 100%;
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  outline: none;
  padding: 8px 0;
  letter-spacing: -0.02em;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.title-input::placeholder { color: #c1cad7; }
.title-input:focus { border-bottom-color: var(--blue); }

.editor-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.editor-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: #fafbfc;
  gap: 12px;
}

.editor-hint {
  font-size: 12px;
  color: var(--text-muted);
  flex: 1;
  text-align: right;
}

.editor-mode-toggle {
  display: flex;
  background: #f1f5f9;
  border-radius: 7px;
  padding: 3px;
  gap: 2px;
  flex-shrink: 0;
}

.mode-btn {
  padding: 4px 14px;
  border: none;
  background: transparent;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.mode-btn.active { background: #fff; color: var(--blue); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.mode-btn:hover:not(.active) { color: var(--text-primary); }

.html-editor {
  display: block;
  width: 100%;
  height: 620px;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #334155;
  background: #f8fafc;
  border: none;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}
.html-editor:focus { background: #fff; }

/* ── 协作者卡片 ── */
.collab-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
}

.collab-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.collab-add {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.collab-tags { padding: 4px 0; }

.collab-empty {
  font-size: 13px;
  color: var(--text-muted);
  padding: 8px 0;
}

.transfer-row { margin-top: 4px; }
.transfer-controls { display: flex; gap: 8px; margin-top: 8px; }

/* ── 右侧元数据面板 ── */
.meta-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.meta-section {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px;
}

.meta-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.field-group { margin-bottom: 12px; }
.field-group:last-child { margin-bottom: 0; }

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 5px;
}

/* ── 封面图 ── */
.cover-upload {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 2px dashed var(--border);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s;
}
.cover-upload:hover { border-color: var(--blue); }

.cover-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--text-muted);
  background: #f8fafc;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s, color 0.2s;
}
.cover-upload:hover .cover-placeholder { background: #eff6ff; color: var(--blue); }
.cover-hint { font-size: 11px; color: var(--text-muted); }

.cover-actions-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.cover-action-btn {
  flex: 1;
  padding: 5px 0;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.cover-action-btn:hover { border-color: #cbd5e1; background: #f8fafc; color: var(--text-primary); }
.cover-action-btn.danger { color: #ef4444; }
.cover-action-btn.danger:hover { border-color: #fca5a5; background: #fef2f2; }

.community-tags { padding: 2px 0 6px; }

.community-hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}

/* ── Element Plus 覆写 ── */
:deep(.el-button) { border-radius: 7px; font-weight: 500; }
:deep(.el-button--primary) { background: var(--blue); border-color: var(--blue); }
:deep(.el-button--primary:hover) { background: #0080e6; border-color: #0080e6; }
:deep(.el-button--success) { background: #22c55e; border-color: #22c55e; }
:deep(.el-button--default) { background: #fff; border-color: var(--border); color: var(--text-primary); }
:deep(.el-input__wrapper) { box-shadow: 0 0 0 1px var(--border); border-radius: 7px; }
:deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0,149,255,0.1); }
:deep(.el-select .el-input__wrapper) { border-radius: 7px; }
</style>
