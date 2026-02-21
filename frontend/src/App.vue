<template>
  <!-- 未登录页面（登录、忘记密码、重置密码、初始设置）：无侧边栏和顶栏 -->
  <div v-if="!showLayout" class="fullscreen-container">
    <router-view />
  </div>

  <!-- 已登录页面：带侧边栏和顶栏 -->
  <el-container v-else class="app-container">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="app-aside" :class="{ collapsed: sidebarCollapsed }">
      <div class="logo">
        <img v-if="!sidebarCollapsed" src="/openGecko-Horizontal.png" alt="openGecko" class="logo-img" />
        <img v-else src="/openGecko-icon.png" alt="openGecko" class="logo-icon" onerror="this.style.display='none'" />
      </div>
      <el-menu
        :default-active="route.path"
        router
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        background-color="#ffffff"
        text-color="#64748b"
        active-text-color="#0095ff"
      >
        <!-- 社区工作台 - 核心入口 -->
        <el-menu-item index="/community">
          <el-icon><House /></el-icon>
          <span>社区工作台</span>
        </el-menu-item>
        <el-menu-item index="/my-work">
          <el-icon><Checked /></el-icon>
          <span>我的工作</span>
        </el-menu-item>
        <!-- 内容管理 -->
        <el-sub-menu index="content">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>内容管理</span>
          </template>
          <el-menu-item index="/contents">
            <el-icon><List /></el-icon>
            <span>内容列表</span>
          </el-menu-item>
          <el-menu-item index="/content-calendar">
            <el-icon><Calendar /></el-icon>
            <span>内容日历</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/publish">
          <el-icon><Promotion /></el-icon>
          <span>发布管理</span>
        </el-menu-item>
        <!-- 社区治理 -->
        <el-sub-menu index="governance">
          <template #title>
            <el-icon><Stamp /></el-icon>
            <span>社区治理</span>
          </template>
          <el-menu-item index="/governance">
            <el-icon><DataLine /></el-icon>
            <span>治理概览</span>
          </el-menu-item>
          <el-menu-item index="/committees">
            <el-icon><Avatar /></el-icon>
            <span>委员会</span>
          </el-menu-item>
          <el-menu-item index="/meetings">
            <el-icon><Calendar /></el-icon>
            <span>会议管理</span>
          </el-menu-item>
        </el-sub-menu>
        <!-- 社区设置（管理员及超管可见）-->
        <el-menu-item v-if="isSuperuser || isAdminInCurrentCommunity" index="/community-settings">
          <el-icon><Setting /></el-icon>
          <span>社区设置</span>
        </el-menu-item>
        <!-- 超管专属区 -->
        <template v-if="isSuperuser">
          <el-divider style="margin: 8px 0" />
          <el-menu-item index="/community-overview">
            <el-icon><OfficeBuilding /></el-icon>
            <span>社区总览</span>
          </el-menu-item>
          <el-menu-item index="/communities">
            <el-icon><Setting /></el-icon>
            <span>社区管理</span>
          </el-menu-item>
          <el-sub-menu index="people">
            <template #title>
              <el-icon><UserFilled /></el-icon>
              <span>人员管理</span>
            </template>
            <el-menu-item index="/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/workload">
              <el-icon><TrendCharts /></el-icon>
              <span>工作量总览</span>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
      <!-- 收缩切换按钮 -->
      <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
        <svg v-if="sidebarCollapsed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <community-switcher v-if="showCommunitySwitcher" />
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ user?.username || '用户' }}</span>
              <el-tag v-if="isSuperuser" size="small" type="danger" style="margin-left: 6px">超级管理员</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>{{ user?.email }}</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis, Document, Promotion, Setting,
  OfficeBuilding, UserFilled, User, Stamp, DataLine, Avatar,
  Calendar, Upload, List, Checked, TrendCharts, House
} from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'
import { useCommunityStore } from './stores/community'
import { getUserInfo } from './api/auth'
import CommunitySwitcher from './components/CommunitySwitcher.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const user = computed(() => authStore.user)
const isSuperuser = computed(() => authStore.isSuperuser)

// 侧边栏收缩状态（持久化到 localStorage）
const sidebarCollapsed = ref(localStorage.getItem('sidebar_collapsed') === 'true')
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar_collapsed', String(sidebarCollapsed.value))
}
const isAdminInCurrentCommunity = computed(() => {
  const cid = communityStore.currentCommunityId
  return cid ? authStore.isAdminInCommunity(cid) : false
})

// 判断是否显示侧边栏和顶栏布局
// 登录页、初始设置页、忘记密码页、重置密码页不显示
const showLayout = computed(() => {
  const noLayoutRoutes = ['Login', 'InitialSetup', 'ForgotPassword', 'ResetPassword']
  return !noLayoutRoutes.includes(route.name as string)
})

// 判断是否显示社区选择下拉框
// 社区总览、社区管理、用户管理、我的工作页面不显示
const showCommunitySwitcher = computed(() => {
  const hideSwitcherRoutes = [
    'CommunityOverview',
    'CommunityManage',
    'UserManage',
    'WorkloadOverview',
    'MyWork',
  ]
  return !hideSwitcherRoutes.includes(route.name as string)
})

onMounted(async () => {
  if (authStore.isAuthenticated) {
    // Always fetch user info and communities to ensure they're up to date
    if (!authStore.user || authStore.communities.length === 0) {
      try {
        const userInfo = await getUserInfo()
        authStore.setUser(userInfo.user)
        authStore.setCommunities(userInfo.communities)
        
        // Set the first community as default if not already set
        if (userInfo.communities.length > 0) {
          const currentCommunityId = localStorage.getItem('current_community_id')
          if (!currentCommunityId) {
            localStorage.setItem('current_community_id', String(userInfo.communities[0].id))
          }
        }
      } catch {
        // If failed to get user info, clear auth
      }
    }
  }
})

function handleCommand(command: string) {
  if (command === 'logout') {
    authStore.clearAuth()
    router.push('/login')
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #1e293b;
}

.fullscreen-container {
  width: 100%;
  height: 100vh;
  overflow: auto;
}

.app-container {
  height: 100vh;
}

.app-aside {
  background-color: #ffffff;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid #e2e8f0;
  transition: width 0.22s ease;
  display: flex;
  flex-direction: column;
  position: relative;
}

.app-aside::-webkit-scrollbar {
  width: 4px;
}

.app-aside::-webkit-scrollbar-track {
  background: transparent;
}

.app-aside::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  min-height: 64px;
  flex-shrink: 0;
}

.logo-img {
  width: 100%;
  max-width: 180px;
  height: auto;
}

.logo-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s ease;
}

.user-info:hover {
  color: #0095ff;
}

.app-main {
  background-color: #f5f7fa;
  overflow-y: auto;
  padding: 0;
}

.el-menu {
  border-right: none !important;
  flex: 1;
}

/* 取消 el-menu collapse 模式的固定宽度限制 */
.app-aside.collapsed .el-menu--collapse {
  width: 64px !important;
}

/* 收缩切换按钮 */
.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 44px;
  background: none;
  border: none;
  border-top: 1px solid #e2e8f0;
  cursor: pointer;
  color: #94a3b8;
  flex-shrink: 0;
  transition: color 0.15s, background 0.15s;
  position: sticky;
  bottom: 0;
  background: #fff;
}
.sidebar-toggle:hover {
  color: #0095ff;
  background: #f8fafc;
}

/* LFX-style sidebar menu items */
.app-aside .el-menu-item {
  border-radius: 8px;
  margin: 2px 8px;
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.app-aside .el-menu-item:hover {
  background-color: #f8fafc !important;
  color: #1e293b !important;
}

.app-aside .el-menu-item.is-active {
  background-color: #eff6ff !important;
  color: #0095ff !important;
}

.app-aside .el-sub-menu .el-sub-menu__title {
  border-radius: 8px;
  margin: 2px 8px;
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  font-weight: 500;
}

.app-aside .el-sub-menu .el-sub-menu__title:hover {
  background-color: #f8fafc !important;
}

.app-aside .el-sub-menu .el-sub-menu__title {
  color: #64748b !important;
}

.app-aside .el-sub-menu.is-active .el-sub-menu__title {
  color: #0095ff !important;
}

.app-aside .el-sub-menu .el-menu-item {
  padding-left: 52px !important;
  margin: 1px 8px;
  height: 38px;
  line-height: 38px;
  font-size: 13px;
}
</style>
