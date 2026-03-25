<template>
  <div class="plug-card" @click="$emit('click', plug)">
    <div class="plug-header">
      <div class="plug-location">{{ plug.location || 'ไม่ระบุ' }}</div>
      <div 
        class="plug-status" 
        :class="plug.online_status"
        :title="plug.online_status"
      ></div>
    </div>
    <div class="plug-icon">🔌</div>
    <div class="plug-name">{{ plug.name }}</div>
    <div class="plug-code">{{ plug.plug_code }}</div>
    <button 
      class="plug-toggle"
      :class="{ on: plug.is_on }"
      @click.stop="$emit('toggle', plug)"
    >
      {{ plug.is_on ? '⚡ เปิดอยู่' : '○ ปิดอยู่' }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  plug: {
    type: Object,
    required: true
  }
})

defineEmits(['toggle', 'click'])
</script>

<style scoped>
.plug-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  width: 160px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.plug-card:hover {
  border-color: var(--text3);
}

.plug-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.plug-location {
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.plug-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.plug-status.online {
  background: var(--accent);
}

.plug-status.offline {
  background: var(--text3);
}

.plug-icon {
  font-size: 22px;
  margin-bottom: 6px;
}

.plug-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plug-code {
  font-size: 11px;
  color: var(--text3);
  margin-bottom: 12px;
  font-family: 'DM Mono', monospace;
}

.plug-toggle {
  width: 100%;
  padding: 7px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  background: var(--surface2);
  color: var(--text2);
  transition: all 0.2s;
}

.plug-toggle.on {
  background: var(--accent);
  color: #000;
  border-color: transparent;
}

.plug-toggle:hover {
  filter: brightness(1.1);
}
</style>
