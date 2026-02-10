<template>
  <el-tag
    :type="tagType"
    :effect="effect"
    :size="size"
    class="role-badge"
  >
    <el-icon v-if="showIcon" class="role-icon">
      <component :is="roleIcon" />
    </el-icon>
    {{ displayText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Star, StarFilled, User, UserFilled } from '@element-plus/icons-vue'

interface Props {
  role: string
  size?: 'large' | 'default' | 'small'
  effect?: 'light' | 'dark' | 'plain'
  showIcon?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
  effect: 'light',
  showIcon: true
})

// Role display mapping
const roleConfig: Record<string, { text: string; type: string; icon: any }> = {
  chair: { text: '主席', type: 'danger', icon: StarFilled },
  vice_chair: { text: '副主席', type: 'warning', icon: Star },
  secretary: { text: '秘书长', type: 'primary', icon: UserFilled },
  member: { text: '委员', type: 'info', icon: User },
  observer: { text: '观察员', type: '', icon: User }
}

const displayText = computed(() => {
  const config = roleConfig[props.role]
  return config ? config.text : props.role
})

const tagType = computed(() => {
  const config = roleConfig[props.role]
  return config ? config.type : ''
})

const roleIcon = computed(() => {
  const config = roleConfig[props.role]
  return config ? config.icon : User
})
</script>

<style scoped>
.role-badge {
  margin-right: 4px;
}

.role-icon {
  margin-right: 4px;
}
</style>
