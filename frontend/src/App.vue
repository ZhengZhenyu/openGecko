<template>
  <!-- 未登录页面（登录、忘记密码、重置密码、初始设置）：无侧边栏和顶栏 -->
  <div v-if="!showLayout" class="fullscreen-container">
    <router-view />
  </div>

  <!-- 已登录页面：带侧边栏和顶栏 -->
  <el-container v-else class="app-container">
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <el-icon :size="24"><Collection /></el-icon>
        <span>OmniContent</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#1d1e1f"
        text-color="#bbb"
        active-text-color="#409eff"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        <el-menu-item index="/community-overview">
          <el-icon><OfficeBuilding /></el-icon>
          <span>社区总览</span>
        </el-menu-item>
        <el-menu-item index="/contents">
          <el-icon><Document /></el-icon>
          <span>内容管理</span>
        </el-menu-item>
        <el-menu-item index="/publish">
          <el-icon><Promotion /></el-icon>
          <span>发布管理</span>
        </el-menu-item>
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
          <el-menu-item index="/committees/batch-manage">
            <el-icon><Upload /></el-icon>
            <span>批量管理</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>渠道设置</span>
        </el-menu-item>
        <el-menu-item v-if="isSuperuser" index="/communities">
          <el-icon><OfficeBuilding /></el-icon>
          <span>社区管理</span>
        </el-menu-item>
        <el-menu-item v-if="isSuperuser" index="/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <community-switcher />
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
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Collection, DataAnalysis, Document, Promotion, Setting, 
  OfficeBuilding, UserFilled, User, Stamp, DataLine, Avatar, 
  Calendar, Upload 
} from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'
import { getUserInfo } from './api/auth'
import CommunitySwitcher from './components/CommunitySwitcher.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)
const isSuperuser = computed(() => authStore.isSuperuser)

// 判断是否显示侧边栏和顶栏布局
// 登录页、初始设置页、忘记密码页、重置密码页不显示
const showLayout = computed(() => {
  const noLayoutRoutes = ['Login', 'InitialSetup', 'ForgotPassword', 'ResetPassword']
  return !noLayoutRoutes.includes(route.name as string)
})

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      const userInfo = await getUserInfo()
      authStore.setUser(userInfo.user)
      authStore.setCommunities(userInfo.communities)
    } catch {
      // If failed to get user info, clear auth
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
  background-color: #1d1e1f;
  overflow-y: auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #333;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 56px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
}

.user-info:hover {
  color: #409eff;
}

.app-main {
  background-color: #f5f7fa;
  overflow-y: auto;
}

.el-menu {
  border-right: none !important;
}
</style>
