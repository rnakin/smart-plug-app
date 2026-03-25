<template>
  <div class="apill" :class="alert.severity">
    <span>{{ alertIcon }}</span>
    <span class="apill-txt">{{ alert.title }}</span>
    <span class="apill-act" @click="$emit('acknowledge', alert.id)">รับทราบ →</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  alert: {
    type: Object,
    required: true
  }
})

defineEmits(['acknowledge'])

const alertIcon = computed(() => {
  if (props.alert.severity === 'danger') return '🔴'
  return '⚠️'
})
</script>

<style scoped>
.apill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.apill.warn {
  background: rgba(255, 170, 58, 0.1);
  border: 1px solid rgba(255, 170, 58, 0.3);
  color: var(--warn);
}

.apill.danger {
  background: rgba(255, 77, 106, 0.1);
  border: 1px solid rgba(255, 77, 106, 0.3);
  color: var(--danger);
}

.apill-txt {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.apill-act {
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.apill-act:hover {
  opacity: 0.8;
}
</style>
