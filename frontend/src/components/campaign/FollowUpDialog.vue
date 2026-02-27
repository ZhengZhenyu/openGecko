<template>
  <el-dialog
    v-model="visible"
    :title="`跟进记录 — ${contact?.person?.display_name ?? ''}`"
    width="440px"
    destroy-on-close
    @closed="$emit('closed')"
  >
    <el-form :model="form" label-width="80px">
      <el-form-item label="跟进方式" required>
        <el-select v-model="form.action" style="width: 100%">
          <el-option label="发送邮件" value="sent_email" />
          <el-option label="电话沟通" value="made_call" />
          <el-option label="微信联系" value="sent_wechat" />
          <el-option label="面对面会谈" value="in_person_meeting" />
          <el-option label="收到回复" value="got_reply" />
          <el-option label="备注" value="note" />
        </el-select>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="form.content" type="textarea" :rows="3" placeholder="跟进内容摘要" />
      </el-form-item>
      <el-form-item label="结果">
        <el-input v-model="form.outcome" placeholder="跟进结果/进展" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { addActivity } from '../../api/campaign'
import type { ContactOut } from '../../api/campaign'

const props = defineProps<{
  modelValue: boolean
  campaignId: number
  contact: ContactOut | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved'): void
  (e: 'closed'): void
}>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const saving = ref(false)
const form = ref({ action: 'note', content: '', outcome: '' })

watch(() => props.contact, () => {
  form.value = { action: 'note', content: '', outcome: '' }
})

async function handleSave() {
  if (!props.contact) return
  saving.value = true
  try {
    await addActivity(props.campaignId, props.contact.id, {
      action: form.value.action,
      content: form.value.content || undefined,
      outcome: form.value.outcome || undefined,
    })
    visible.value = false
    ElMessage.success('跟进记录已保存')
    emit('saved')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>
