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
      <MdEditorV3
        v-model="form.content_markdown"
        :preview="true"
        language="zh-CN"
        style="height: 600px"
      />
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
import { fetchContent, createContent, updateContent, uploadCoverImage } from '../api/content'

const route = useRoute()
const router = useRouter()
const saving = ref(false)
const coverInput = ref<HTMLInputElement | null>(null)
const coverImageUrl = ref<string | null>(null)

const contentId = computed(() => route.params.id ? Number(route.params.id) : null)
const isNew = computed(() => !contentId.value)

const form = ref({
  title: '',
  content_markdown: '',
  source_type: 'contribution',
  author: '',
  category: '',
  tags: [] as string[],
})
const tagsInput = ref('')

onMounted(async () => {
  if (contentId.value) {
    const data = await fetchContent(contentId.value)
    form.value = {
      title: data.title,
      content_markdown: data.content_markdown,
      source_type: data.source_type,
      author: data.author,
      category: data.category,
      tags: data.tags,
    }
    tagsInput.value = data.tags.join(', ')
    coverImageUrl.value = data.cover_image || null
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
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.actions { display: flex; gap: 8px; }
.meta-card :deep(.el-form-item) { margin-bottom: 0; }

.cover-upload-area {
  width: 320px;
}

.cover-preview {
  position: relative;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
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
  padding: 8px;
  justify-content: center;
  background: #fafafa;
}

.cover-placeholder {
  width: 100%;
  height: 136px;
  border: 2px dashed #dcdfe6;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #909399;
  gap: 4px;
  transition: border-color 0.2s;
}

.cover-placeholder:hover {
  border-color: #409eff;
  color: #409eff;
}

.cover-placeholder span {
  font-size: 13px;
}

.cover-placeholder .hint {
  font-size: 11px;
  color: #c0c4cc;
}
</style>
