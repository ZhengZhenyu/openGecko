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
      path: '/users',
      name: 'UserManage',
      component: () => import('../views/UserManage.vue'),
      meta: { requiresAuth: true, requiresSuperuser: true },
    },
  ],
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const communityStore = useCommunityStore()
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresSuperuser = to.meta.requiresSuperuser === true

  // If authenticated but user info not loaded, fetch it first
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      const { getUserInfo } = await import('../api/auth')
      const userInfo = await getUserInfo()
      // Backend returns user data directly with communities array
      // We need to separate them for the store
      const { communities, ...userData } = userInfo
      authStore.setUser(userData as any)
      authStore.setCommunities(communities)
      
      // Set default community if available and not already set
      if (communities.length > 0 && !communityStore.currentCommunityId) {
        communityStore.setCommunity(communities[0].id)
      }
      
      console.log('User info loaded:', userData.username, 'is_superuser:', userData.is_superuser)
    } catch (error) {
      // If failed to get user info, clear auth and redirect to login
      console.error('Failed to load user info:', error)
      authStore.clearAuth()
      if (requiresAuth) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    }
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if not authenticated
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (requiresSuperuser && !authStore.isSuperuser) {
    // Redirect to dashboard if not superuser
    console.warn('Access denied: requires superuser. Current user:', authStore.user)
    next({ name: 'Dashboard' })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    // Redirect to dashboard if already logged in
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
