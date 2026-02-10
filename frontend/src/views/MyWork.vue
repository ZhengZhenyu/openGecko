<template>
  <div class="my-work-container">
    <el-card class="header-card">
      <div class="header">
        <div>
          <h2><el-icon><User /></el-icon> 我的工作</h2>
          <p class="subtitle">查看和管理我负责的所有任务</p>
        </div>
        <div class="stats">
          <el-statistic title="计划中" :value="totalPlanning">
            <template #prefix><el-icon color="#909399"><Clock /></el-icon></template>
          </el-statistic>
          <el-statistic title="进行中" :value="totalInProgress">
            <template #prefix><el-icon color="#E6A23C"><Loading /></el-icon></template>
          </el-statistic>
          <el-statistic title="已完成" :value="totalCompleted">
            <template #prefix><el-icon color="#67C23A"><CircleCheck /></el-icon></template>
          </el-statistic>
        </div>
      </div>
    </el-card>

    <el-card class="filter-card">
      <el-radio-group v-model="filterStatus" @change="loadData">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="planning">计划中</el-radio-button>
        <el-radio-button value="in_progress">进行中</el-radio-button>
        <el-radio-button value="completed">已完成</el-radio-button>
      </el-radio-group>
      <el-radio-group v-model="filterType" class="ml20">
        <el-radio-button value="all">全部类型</el-radio-button>
        <el-radio-button value="content">内容</el-radio-button>
        <el-radio-button value="meeting">会议</el-radio-button>
      </el-radio-group>
    </el-card>

    <el-card v-loading="loading">
      <el-empty v-if="filteredItems.length === 0" description="暂无任务" />
      <div v-else class="items">
        <div 
          v-for="item in filteredItems" 
          :key="`${item.type}-${item.id}`" 
          class="item"
          @click="goToDetail(item)"
        >
          <div class="item-header">
            <div class="item-title">
              <el-tag :type="item.type === 'content' ? 'primary' : 'success'" size="small">
                {{ item.type === 'content' ? '内容' : '会议' }}
              </el-tag>
              <span>{{ item.title }}</span>
            </div>
            <el-select 
              v-model="item.work_status" 
              @change="updateStatus(item)" 
              @click.stop
              size="small" 
              style="width: 120px"
            >
              <el-option label="计划中" value="planning" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
            </el-select>
          </div>
          <div class="item-meta">
            <span><el-icon><UserFilled /></el-icon> {{ item.creator_name || '未知' }}</span>
            <span><el-icon><User /></el-icon> {{ item.assignee_count }} 人</span>
            <span><el-icon><Calendar /></el-icon> {{ formatDate(item.updated_at) }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Clock, Loading, CircleCheck, UserFilled, Calendar } from '@element-plus/icons-vue'
import axios from '../api'

const router = useRouter()

interface Item {
  id: number
  type: string
  title: string
  work_status: string
  creator_name?: string
  assignee_count: number
  updated_at: string
}

const loading = ref(false)
const data = ref<any>(null)
const filterStatus = ref('all')
const filterType = ref('all')

const allItems = computed(() => {
  if (!data.value) return []
  return [...data.value.contents, ...data.value.meetings]
})

const filteredItems = computed(() => {
  let items = allItems.value
  if (filterStatus.value !== 'all') items = items.filter((i: Item) => i.work_status === filterStatus.value)
  if (filterType.value !== 'all') items = items.filter((i: Item) => i.type === filterType.value)
  return items
})

const totalPlanning = computed(() => 
  data.value ? (data.value.content_stats.planning + data.value.meeting_stats.planning) : 0
)
const totalInProgress = computed(() => 
  data.value ? (data.value.content_stats.in_progress + data.value.meeting_stats.in_progress) : 0
)
const totalCompleted = computed(() => 
  data.value ? (data.value.content_stats.completed + data.value.meeting_stats.completed) : 0
)

const formatDate = (d: string) => new Date(d).toLocaleDateString('zh-CN')

const loadData = async () => {
  loading.value = true
  try {
    const { data: res } = await axios.get('/users/me/dashboard')
    data.value = res
  } catch (error: any) {
    ElMessage.error('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const updateStatus = async (item: Item) => {
  const url = `/users/me/${item.type === 'content' ? 'contents' : 'meetings'}/${item.id}/work-status`
  try {
    await axios.patch(url, { work_status: item.work_status })
    ElMessage.success('状态已更新')
    loadData()
  } catch (error: any) {
    ElMessage.error('更新失败: ' + (error.response?.data?.detail || error.message))
    loadData()
  }
}

const goToDetail = (item: Item) => {
  if (item.type === 'content') {
    router.push(`/contents/${item.id}/edit`)
  } else if (item.type === 'meeting') {
    router.push(`/meetings/${item.id}`)
  }
}

onMounted(() => loadData())
</script>

<style scoped lang="scss">
.my-work-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  h2 {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 8px;
  }

  .subtitle {
    margin: 0;
    color: #909399;
  }

  .stats {
    display: flex;
    gap: 40px;
  }
}

.filter-card {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    display: flex;
    align-items: center;
  }

  .ml20 {
    margin-left: 20px;
  }
}

.items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item {
  padding: 16px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: #409EFF;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.item-title {
  display: flex;
  align-items: center;
  gap: 10px;

  span {
    font-weight: 500;
  }
}

.item-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #606266;

  span {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}
</style>
