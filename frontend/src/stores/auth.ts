import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface Community {
  id: number
  name: string
  slug: string
  description?: string
  url?: string
  logo_url?: string
  is_active: boolean
  role?: string  // User's role in this community: 'admin', 'user', or 'superuser'
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const user = ref<User | null>(null)
  const communities = ref<Community[]>([])

  // Computed
  const isAuthenticated = computed(() => !!token.value)
  const isSuperuser = computed(() => user.value?.is_superuser || false)

  // Role utilities — 使用 community_id 查询当前用户在该社区中的角色
  function getRoleInCommunity(communityId: number): string | null {
    if (user.value?.is_superuser) return 'superuser'
    const community = communities.value.find((c) => c.id === communityId)
    return community?.role ?? null
  }

  function isAdminInCommunity(communityId: number): boolean {
    const role = getRoleInCommunity(communityId)
    return role === 'superuser' || role === 'admin'
  }

  function getCommunityById(communityId: number): Community | null {
    return communities.value.find((c) => c.id === communityId) ?? null
  }

  // Actions
  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('auth_token', newToken)
  }

  function setUser(newUser: User) {
    user.value = newUser
  }

  function setCommunities(newCommunities: Community[]) {
    communities.value = newCommunities
  }

  function clearAuth() {
    token.value = null
    user.value = null
    communities.value = []
    localStorage.removeItem('auth_token')
    localStorage.removeItem('current_community_id')
  }

  // Initialize from localStorage on store creation
  function initialize() {
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      token.value = storedToken
    }
  }

  // Initialize immediately
  initialize()

  return {
    // State
    token,
    user,
    communities,
    // Computed
    isAuthenticated,
    isSuperuser,
    // Role utilities
    getRoleInCommunity,
    isAdminInCommunity,
    getCommunityById,
    // Actions
    setToken,
    setUser,
    setCommunities,
    clearAuth,
    initialize,
  }
})
