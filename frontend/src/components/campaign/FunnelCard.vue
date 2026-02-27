<template>
  <div class="funnel-card">
    <h3 class="funnel-title">转化漏斗</h3>
    <div v-if="funnel" class="funnel-list">
      <div v-for="step in steps" :key="step.key" class="funnel-item">
        <div class="funnel-label">
          <span class="funnel-dot" :style="{ background: step.color }" />
          {{ step.label }}
        </div>
        <div class="funnel-bar-wrap">
          <div
            class="funnel-bar"
            :style="{
              width: funnel.total ? (funnel[step.key] / funnel.total * 100) + '%' : '0%',
              background: step.color,
            }"
          />
        </div>
        <span class="funnel-count">{{ funnel[step.key] }}</span>
      </div>
      <div class="funnel-total">共 {{ funnel.total }} 人</div>
    </div>
    <div v-else class="funnel-empty">暂无数据</div>
  </div>
</template>

<script setup lang="ts">
import type { CampaignFunnel } from '../../api/campaign'

defineProps<{ funnel: CampaignFunnel | null }>()

const steps: { key: keyof CampaignFunnel; label: string; color: string }[] = [
  { key: 'pending', label: '待联系', color: '#94a3b8' },
  { key: 'contacted', label: '已联系', color: '#0095ff' },
]
</script>

<style scoped>
.funnel-card {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.funnel-title {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.funnel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.funnel-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.funnel-label {
  display: flex;
  align-items: center;
  gap: 5px;
  width: 64px;
  font-size: 12px;
  color: #475569;
  flex-shrink: 0;
}

.funnel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.funnel-bar-wrap {
  flex: 1;
  height: 10px;
  background: #f1f5f9;
  border-radius: 5px;
  overflow: hidden;
}

.funnel-bar {
  height: 100%;
  border-radius: 5px;
  min-width: 2px;
  transition: width 0.3s;
}

.funnel-count {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  width: 28px;
  text-align: right;
}

.funnel-total {
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
  margin-top: 4px;
}

.funnel-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 20px 0;
}
</style>
