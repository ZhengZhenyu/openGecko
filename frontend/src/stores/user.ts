import { defineStore } from 'pinia'
import { computed } from 'vue'
import { useAuthStore } from './auth'
import { useCommunityStore } from './community'

export const useUserStore = defineStore('user', () => {
  const authStore = useAuthStore()
  const communityStore = useCommunityStore()

  // Check if user is admin of the current community
  const isCommunityAdmin = computed(() => {
    if (authStore.isSuperuser) return true
    
    const currentCommunityId = communityStore.currentCommunityId
    if (!currentCommunityId) return false
    
    const community = authStore.communities.find(c => c.id === currentCommunityId)
    return community?.role === 'admin' || community?.role === 'superuser'
  })

  const currentUser = computed(() => authStore.user)

  return {
    isCommunityAdmin,
    currentUser
  }
})
