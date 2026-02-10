<template>
  <div class="community-switcher">
    <el-select
      v-model="selectedCommunityId"
      :placeholder="communities.length === 0 ? '暂无社区' : '选择社区'"
      :disabled="communities.length === 0"
      size="default"
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
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { useCommunityStore } from '../stores/community'

const authStore = useAuthStore()
const communityStore = useCommunityStore()

const communities = computed(() => authStore.communities)
const selectedCommunityId = ref<number | null>(communityStore.currentCommunityId)

// Watch for external changes to current community
watch(
  () => communityStore.currentCommunityId,
  (newId) => {
    selectedCommunityId.value = newId
  }
)

const handleCommunityChange = (communityId: number) => {
  const community = communities.value.find((c) => c.id === communityId)
  if (community) {
    communityStore.setCommunity(communityId)
    ElMessage.success(`已切换到社区: ${community.name}`)
    // Reload page to refresh data for new community
    window.location.reload()
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
