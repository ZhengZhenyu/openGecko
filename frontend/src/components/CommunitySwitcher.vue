<template>
  <div class="community-switcher">
    <el-select
      :model-value="selectedCommunityId"
      :placeholder="communities.length === 0 ? '暂无社区' : '选择社区'"
      :disabled="communities.length === 0"
      size="default"
      filterable
      @change="handleCommunityChange"
    >
      <el-option
        v-for="community in communities"
        :key="community.id"
        :label="community.name"
        :value="community.id"
      >
        <div class="community-option">
          <span class="community-name">{{ community.name }}</span>
          <span class="community-slug">{{ community.slug }}</span>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'

const router = useRouter()
const authStore = useAuthStore()
const communityStore = useCommunityStore()

const communities = computed(() => authStore.communities)
const selectedCommunityId = computed(() => communityStore.currentCommunityId)

// Auto-select first community if no community is selected and communities are available
onMounted(() => {
  if (!selectedCommunityId.value && communities.value.length > 0) {
    communityStore.setCommunity(communities.value[0].id)
  }
})

// Watch for changes in communities list
watch(
  () => communities.value.length,
  (newLength) => {
    // If we have communities but no selected community, select the first one
    if (newLength > 0 && !selectedCommunityId.value) {
      communityStore.setCommunity(communities.value[0].id)
    }
  }
)

const handleCommunityChange = (communityId: number) => {
  const community = communities.value.find((c) => c.id === communityId)
  if (community) {
    communityStore.setCommunity(communityId)
    ElMessage.success(`已切换到社区: ${community.name}`)
    
    // Navigate to community overview instead of reloading
    // This allows the app to handle data refresh internally
    router.push('/community-overview')
  }
}
</script>

<style scoped lang="scss">
.community-switcher {
  .el-select {
    min-width: 200px;
  }
}

.community-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .community-name {
    font-weight: 500;
  }

  .community-slug {
    font-size: 12px;
    color: #909399;
    margin-left: 8px;
  }
}
</style>
