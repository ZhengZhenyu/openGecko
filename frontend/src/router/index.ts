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
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/contents',
      name: 'ContentList',
      component: () => import('../views/ContentList.vue'),
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
      
      // Set default community if available and not already set (optional now)
      // Users can work without a default community
      if (userInfo.communities.length > 0 && !communityStore.currentCommunityId) {
        communityStore.setCommunity(userInfo.communities[0].id)
      }
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
    // Redirect to dashboard if not superuser
    console.log('[Router Guard] Redirecting to dashboard - not superuser')
    next({ name: 'Dashboard' })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    // Redirect to dashboard if already logged in
    console.log('[Router Guard] Redirecting to dashboard - already logged in')
    next({ name: 'Dashboard' })
  } else {
    console.log('[Router Guard] Allowing navigation')
    next()
  }
})

export default router
