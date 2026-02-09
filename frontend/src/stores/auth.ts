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
    // Actions
    setToken,
    setUser,
    setCommunities,
    clearAuth,
    initialize,
  }
})
