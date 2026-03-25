<template>
  <div 
    class="htab" 
    :class="{ active }"
    @click="$emit('select', house)"
  >
    <span class="htab-emoji">{{ house.emoji || '🏠' }}</span>
    <span class="htab-name">{{ house.house_name }}</span>
  </div>
</template>

<script setup>
defineProps({
  house: {
    type: Object,
    required: true
  },
  active: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])
</script>

<style scoped>
.htab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.htab:hover {
  border-color: var(--text3);
  color: var(--text);
}

.htab.active {
  background: var(--accent-dim);
  border-color: var(--accent);
  color: var(--accent);
}

.htab-emoji {
  font-size: 16px;
}
</style>
