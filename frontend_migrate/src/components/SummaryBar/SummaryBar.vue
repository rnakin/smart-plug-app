<template>
  <div class="sum-bar">
    <div class="ss">
      <div class="ssl">ปลั๊ก</div>
      <div class="ssv">{{ plugCount }}</div>
    </div>
    <div class="sdiv"></div>
    <div class="ss">
      <div class="ssl">กำลังไฟ</div>
      <div class="ssv acc">{{ totalPower.toLocaleString() }} W</div>
    </div>
    <div class="sdiv"></div>
    <div class="ss">
      <div class="ssl">วันนี้</div>
      <div class="ssv">{{ todayKwh }} kWh</div>
    </div>
    <div class="sdiv"></div>
    <div class="ss">
      <div class="ssl">แจ้งเตือน</div>
      <div class="ssv" :class="{ wrn: alertCount > 0 }">{{ alertCount }} รายการ</div>
    </div>
    <div class="sr">
      <RouterLink to="/dashboard" class="tbtn">Dashboard →</RouterLink>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  plugCount: { type: Number, default: 0 },
  totalPower: { type: Number, default: 0 },
  todayKwh: { type: Number, default: 0 },
  alertCount: { type: Number, default: 0 }
})
</script>

<style scoped>
.sum-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 14px 26px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.ss {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px;
}

.ssl {
  font-size: 11px;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ssv {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  font-family: 'DM Mono', monospace;
}

.ssv.acc {
  color: var(--accent);
}

.ssv.wrn {
  color: var(--warn);
}

.sdiv {
  width: 1px;
  height: 30px;
  background: var(--border);
}

.sr {
  margin-left: auto;
}

.tbtn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.tbtn:hover {
  color: var(--text);
  border-color: var(--text3);
}
</style>
