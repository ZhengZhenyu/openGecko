<template>
  <div class="content-list">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-header">
        <h2>内容管理</h2>
        <div class="actions">
          <el-upload
            :show-file-list="false"
            :before-upload="handleUpload"
            accept=".docx,.md,.markdown"
          >
            <el-button type="success" :icon="Upload">上传文件</el-button>
          </el-upload>
          <el-button type="primary" :icon="Plus" @click="$router.push('/contents/new')">新建内容</el-button>
        </div>
      </div>

      <el-card>
        <div class="filters">
          <el-input v-model="keyword" placeholder="搜索标题..." clearable style="width: 240px" @clear="loadData" @keyup.enter="loadData" />
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadData" style="width: 140px">
            <el-option label="草稿" value="draft" />
            <el-option label="审核中" value="reviewing" />
            <el-option label="已通过" value="approved" />
            <el-option label="已发布" value="published" />
          </el-select>
          <el-select v-model="filterSource" placeholder="来源筛选" clearable @change="loadData" style="width: 140px">
            <el-option label="社区投稿" value="contribution" />
            <el-option label="Release Note" value="release_note" />
            <el-option label="活动总结" value="event_summary" />
          </el-select>
        </div>

        <el-table :data="contents" v-loading="loading" stripe>
          <el-table-column prop="title" label="标题" min-width="240">
            <template #default="{ row }">
              <router-link :to="`/contents/${row.id}/edit`" class="title-link">{{ row.title }}</router-link>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="来源" width="120">
            <template #default="{ row }">{{ sourceLabel(row.source_type) }}</template>
          </el-table-column>
          <el-table-column prop="author" label="作者" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="$router.push(`/contents/${row.id}/edit`)">编辑</el-button>
              <el-button size="small" type="primary" @click="$router.push(`/publish/${row.id}`)">发布</el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="total > pageSize"
          style="margin-top: 16px; justify-content: flex-end"
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { fetchContents, deleteContent, uploadFile, type ContentListItem } from '../api/content'
import { useRouter } from 'vue-router'
import { useCommunityStore } from '../stores/community'

const router = useRouter()
const communityStore = useCommunityStore()
const contents = ref<ContentListItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const filterStatus = ref('')
const filterSource = ref('')

async function loadData() {
  loading.value = true
  try {
    const res = await fetchContents({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      source_type: filterSource.value || undefined,
      keyword: keyword.value || undefined,
    })
    contents.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handlePageChange(p: number) {
  page.value = p
  loadData()
}

async function handleUpload(file: File) {
  try {
    const content = await uploadFile(file)
    ElMessage.success(`文件 "${file.name}" 上传成功`)
    router.push(`/contents/${content.id}/edit`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  }
  return false
}

async function handleDelete(id: number) {
  await deleteContent(id)
  ElMessage.success('已删除')
  loadData()
}

function sourceLabel(s: string) {
  const map: Record<string, string> = { contribution: '社区投稿', release_note: 'Release Note', event_summary: '活动总结' }
  return map[s] || s
}

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布' }
  return map[s] || s
}

function statusType(s: string) {
  const map: Record<string, string> = { draft: 'info', reviewing: 'warning', approved: 'success', published: '' }
  return (map[s] || 'info') as any
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(() => {
  if (communityStore.currentCommunityId) {
    loadData()
  }
})

// Watch for community changes
watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    if (newId) {
      loadData()
    }
  }
)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.actions { display: flex; gap: 12px; }
.filters { display: flex; gap: 12px; margin-bottom: 16px; }
.title-link { color: #333; text-decoration: none; }
.title-link:hover { color: #409eff; }
</style>
