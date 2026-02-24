import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/initial-setup',
      name: 'InitialSetup',
      component: () => import('../views/InitialSetup.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: () => import('../views/ForgotPassword.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/reset-password',
      name: 'ResetPassword',
      component: () => import('../views/ResetPassword.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      redirect: '/community',
    },
    {
      path: '/community',
      name: 'CommunitySandbox',
      component: () => import('../views/CommunitySandbox.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/community-wizard',
      name: 'CommunityWizard',
      component: () => import('../views/CommunityWizard.vue'),
      meta: { requiresAuth: true, requiresSuperuser: true },
    },
    {
      path: '/community-settings/:communityId?',
      name: 'CommunitySettings',
      component: () => import('../views/CommunitySettings.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my-work',
      name: 'MyWork',
      component: () => import('../views/MyWork.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/contents',
      name: 'ContentList',
      component: () => import('../views/ContentList.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/content-calendar',
      name: 'ContentCalendar',
      component: () => import('../views/ContentCalendar.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/contents/new',
      name: 'ContentNew',
      component: () => import('../views/ContentEdit.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/contents/:id/edit',
      name: 'ContentEdit',
      component: () => import('../views/ContentEdit.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/publish/:id?',
      name: 'PublishView',
      component: () => import('../views/PublishView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/communities',
      name: 'CommunityManage',
      component: () => import('../views/CommunityManage.vue'),
      meta: { requiresAuth: true, requiresSuperuser: true },
    },
    {
      path: '/community-overview',
      name: 'CommunityOverview',
      component: () => import('../views/CommunityOverview.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/users',
      name: 'UserManage',
      component: () => import('../views/UserManage.vue'),
      meta: { requiresAuth: true, requiresSuperuser: true },
    },
    {
      path: '/workload',
      name: 'WorkloadOverview',
      component: () => import('../views/WorkloadOverview.vue'),
      meta: { requiresAuth: true, requiresSuperuser: true },
    },
    {
      path: '/committees',
      name: 'CommitteeList',
      component: () => import('../views/CommitteeList.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/committees/:id',
      name: 'CommitteeDetail',
      component: () => import('../views/CommitteeDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/committees/batch-manage',
      name: 'CommitteeMemberManage',
      component: () => import('../views/CommitteeMemberManage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/governance',
      name: 'GovernanceOverview',
      component: () => import('../views/GovernanceOverview.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/meetings',
      name: 'MeetingCalendar',
      component: () => import('../views/MeetingCalendar.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/meetings/:id',
      name: 'MeetingDetail',
      component: () => import('../views/MeetingDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/wechat-stats',
      name: 'WechatStats',
      component: () => import('../views/WechatStats.vue'),
      meta: { requiresAuth: true },
    },
    // Phase 4b 活动管理路由
    {
      path: '/events',
      name: 'Events',
      component: () => import('../views/Events.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/events/new',
      name: 'EventNew',
      component: () => import('../views/EventDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/events/:id',
      name: 'EventDetail',
      component: () => import('../views/EventDetail.vue'),
      meta: { requiresAuth: true },
    },
    // Phase 4a 占位路由 (People)
    {
      path: '/people',
      name: 'People',
      component: () => import('../views/People.vue'),
      meta: { requiresAuth: true },
    },
    // Phase 4c 运营活动路由
    {
      path: '/campaigns',
      name: 'Campaigns',
      component: () => import('../views/Campaigns.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/campaigns/:id',
      name: 'CampaignDetail',
      component: () => import('../views/CampaignDetail.vue'),
      meta: { requiresAuth: true },
    },
    // Phase 4d 生态洞察路由
    {
      path: '/ecosystem',
      name: 'EcosystemList',
      component: () => import('../views/EcosystemList.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ecosystem/:id',
      name: 'EcosystemDetail',
      component: () => import('../views/EcosystemDetail.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const communityStore = useCommunityStore()
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresSuperuser = to.meta.requiresSuperuser === true

  console.log('[Router Guard]', {
    to: to.name,
    from: from.name,
    isAuthenticated: authStore.isAuthenticated,
    hasUser: !!authStore.user,
  })

  // Special case: initial-setup page doesn't need user info loaded
  // It's for default admin to create a new admin account
  if (to.name === 'InitialSetup' && authStore.isAuthenticated) {
    console.log('[Router Guard] Allowing access to InitialSetup for authenticated user')
    next()
    return
  }

  // If authenticated but user info not loaded, fetch it first
  if (authStore.isAuthenticated && !authStore.user) {
    console.log('[Router Guard] Loading user info...')
    try {
      const { getUserInfo } = await import('../api/auth')
      const userInfo = await getUserInfo()
      authStore.setUser(userInfo.user)
      authStore.setCommunities(userInfo.communities)
      
      // Do not auto-select community - pages handle empty state individually
      console.log('[Router Guard] User info loaded successfully')
    } catch (error) {
      // If failed to get user info, clear auth and redirect to login
      console.error('[Router Guard] Failed to load user info:', error)
      authStore.clearAuth()
      if (requiresAuth) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    }
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if not authenticated
    console.log('[Router Guard] Redirecting to login - not authenticated')
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (requiresSuperuser && !authStore.isSuperuser) {
    // Redirect to community sandbox if not superuser
    console.log('[Router Guard] Redirecting to CommunitySandbox - not superuser')
    next({ name: 'CommunitySandbox' })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    // Redirect to community sandbox if already logged in
    console.log('[Router Guard] Redirecting to CommunitySandbox - already logged in')
    next({ name: 'CommunitySandbox' })
  } else {
    console.log('[Router Guard] Allowing navigation')
    next()
  }
})

export default router
