<template>
  <div class="governance-overview">
    <el-empty v-if="!communityStore.currentCommunityId"
      description="请先选择一个社区"
      :image-size="150"
    >
      <p style="color: #909399; font-size: 14px;">使用顶部的社区切换器选择要管理的社区</p>
    </el-empty>

    <template v-else>
      <div class="page-header">
        <h2>社区治理</h2>
        <p>管理委员会、会议和成员</p>
      </div>

      <el-row :gutter="24" class="stats-row">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-icon committee">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.committeeCount }}</div>
              <div class="stat-label">委员会</div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-icon member">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.memberCount }}</div>
              <div class="stat-label">成员</div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-icon meeting">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.upcomingMeetings }}</div>
              <div class="stat-label">即将召开</div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-icon history">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalMeetings }}</div>
              <div class="stat-label">历史会议</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="24" class="content-row">
        <el-col :xs="24" :md="12">
          <el-card class="section-card">
            <template #header>
              <div class="card-header">
                <span>委员会</span>
                <el-button type="primary" link @click="$router.push('/committees')">
                  查看全部
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </template>

            <div v-loading="loadingCommittees">
              <div
                v-for="committee in committees"
                :key="committee.id"
                class="list-item"
                @click="$router.push('/committees/' + committee.id)"
              >
                <div class="item-content">
                  <div class="item-title">{{ committee.name }}</div>
                  <div class="item-meta">
                    <span>{{ committee.member_count }} 名成员</span>
                    <el-tag v-if="!committee.is_active" type="info" size="small">已归档</el-tag>
                  </div>
                </div>
                <el-icon class="item-arrow"><ArrowRight /></el-icon>
              </div>
              <el-empty v-if="committees.length === 0" description="暂无委员会" :image-size="80" />
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-card class="section-card">
            <template #header>
              <div class="card-header">
                <span>近期会议</span>
                <el-button type="primary" link @click="$router.push('/meetings')">
                  查看日历
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </template>

            <div v-loading="loadingMeetings">
              <div
                v-for="meeting in upcomingMeetings"
                :key="meeting.id"
                class="list-item"
                @click="$router.push('/meetings/' + meeting.id)"
              >
                <div class="item-content">
                  <div class="item-title">{{ meeting.title }}</div>
                  <div class="item-meta">
                    <span>{{ formatDateTime(meeting.scheduled_at) }}</span>
                    <el-tag :type="getMeetingStatusType(meeting.status)" size="small">
                      {{ getMeetingStatusText(meeting.status) }}
                    </el-tag>
                  </div>
                </div>
                <el-icon class="item-arrow"><ArrowRight /></el-icon>
              </div>
              <el-empty v-if="upcomingMeetings.length === 0" description="暂无即将召开的会议" :image-size="80" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="isAdmin" class="actions-card">
        <template #header>
          <span>快捷操作</span>
        </template>
        <div class="quick-actions">
          <el-button type="primary" @click="$router.push('/committees?action=create')">
            <el-icon><Plus /></el-icon>
            创建委员会
          </el-button>
          <el-button type="success" @click="$router.push('/meetings?action=create')">
            <el-icon><Plus /></el-icon>
            创建会议
          </el-button>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { OfficeBuilding, UserFilled, Calendar, Clock, ArrowRight, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listCommittees, listMeetings, type Committee, type Meeting } from '@/api/governance'
import { useUserStore } from '@/stores/user'
import { useCommunityStore } from '@/stores/community'

const router = useRouter()
const userStore = useUserStore()
const communityStore = useCommunityStore()
const isAdmin = computed(() => userStore.isCommunityAdmin)
const loadingCommittees = ref(false)
const loadingMeetings = ref(false)
const committees = ref<Committee[]>([])
const upcomingMeetings = ref<Meeting[]>([])

const stats = computed(() => {
  const now = new Date()
  const upcoming = upcomingMeetings.value.filter(
    m => new Date(m.scheduled_at) > now && m.status === 'scheduled'
  )
  return {
    committeeCount: committees.value.filter(c => c.is_active).length,
    memberCount: committees.value.reduce((sum, c) => sum + c.member_count, 0),
    upcomingMeetings: upcoming.length,
    totalMeetings: upcomingMeetings.value.length
  }
})

onMounted(() => {
  if (!communityStore.currentCommunityId) return
  loadData()
})

async function loadData() {
  await Promise.all([loadCommittees(), loadMeetings()])
}

async function loadCommittees() {
  loadingCommittees.value = true
  try {
    const data = await listCommittees({ is_active: true })
    committees.value = data.slice(0, 5)
  } catch (error: any) {
    ElMessage.error(error.message || '加载委员会失败')
  } finally {
    loadingCommittees.value = false
  }
}

async function loadMeetings() {
  loadingMeetings.value = true
  try {
    const now = new Date()
    const startDate = now.toISOString().split('T')[0]
    const endDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    const data = await listMeetings({ start_date: startDate, end_date: endDate, limit: 5 })
    upcomingMeetings.value = data
  } catch (error: any) {
    ElMessage.error(error.message || '加载会议失败')
  } finally {
    loadingMeetings.value = false
  }
}

function formatDateTime(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function getMeetingStatusType(status: string) {
  const map: Record<string, any> = { scheduled: 'primary', in_progress: 'success', completed: 'info', cancelled: 'danger' }
  return map[status] || ''
}

function getMeetingStatusText(status: string) {
  const map: Record<string, string> = { scheduled: '已安排', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }
  return map[status] || status
}
</script>

<style scoped>
.governance-overview { padding: 24px; }
.page-header { margin-bottom: 24px; }
.page-header h2 { margin: 0 0 4px 0; font-size: 24px; font-weight: 600; }
.page-header p { margin: 0; color: var(--el-text-color-secondary); font-size: 14px; }
.stats-row { margin-bottom: 24px; }
.stat-card :deep(.el-card__body) { display: flex; align-items: center; gap: 16px; padding: 20px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 28px; color: white; }
.stat-icon.committee { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.member { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-icon.meeting { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-icon.history { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.stat-content { flex: 1; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--el-text-color-primary); line-height: 1; margin-bottom: 4px; }
.stat-label { font-size: 14px; color: var(--el-text-color-secondary); }
.content-row { margin-bottom: 24px; }
.section-card { height: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.list-item { display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--el-border-color-lighter); cursor: pointer; transition: background 0.2s; }
.list-item:last-child { border-bottom: none; }
.list-item:hover { background: var(--el-fill-color-light); margin: 0 -12px; padding-left: 12px; padding-right: 12px; border-radius: 4px; }
.item-content { flex: 1; }
.item-title { font-size: 15px; font-weight: 500; color: var(--el-text-color-primary); margin-bottom: 4px; }
.item-meta { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--el-text-color-secondary); }
.item-arrow { color: var(--el-text-color-placeholder); font-size: 14px; }
.actions-card { margin-top: 24px; }
.quick-actions { display: flex; gap: 12px; flex-wrap: wrap; }
</style>
