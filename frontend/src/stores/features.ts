import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFeaturesStore = defineStore('features', () => {
  const insightsModule = ref(true) // 默认开启，确保首次渲染前不意外隐藏

  async function fetchFeatures() {
    try {
      const res = await fetch('/api/config/features')
      if (res.ok) {
        const data = await res.json()
        insightsModule.value = data.insights_module ?? true
      }
    } catch {
      // 接口异常时保持默认值（开启），不影响现有功能
    }
  }

  return { insightsModule, fetchFeatures }
})
