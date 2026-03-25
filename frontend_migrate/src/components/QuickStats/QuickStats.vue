<template>
  <div class="qs-row">
    <div class="qs">
      <div class="dot" style="background: var(--accent)"></div>
      เปิดอยู่ <span class="v">{{ online }}</span>
    </div>
    <div class="qs">
      <div class="dot" style="background: var(--warn)"></div>
      แจ้งเตือน <span class="v">{{ alerts }}</span>
    </div>
    <div class="qs">
      ⚡ <span class="v">{{ power.toLocaleString() }}</span> W
    </div>
  </div>
</template>

<script setup>
defineProps({
  online: { type: Number, default: 0 },
  alerts: { type: Number, default: 0 },
  power: { type: Number, default: 0 }
})
</script>

<style scoped>
.qs-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.qs {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text2);
}

.qs .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.qs .v {
  font-weight: 600;
  color: var(--text);
  font-family: 'DM Mono', monospace;
}
</style>
