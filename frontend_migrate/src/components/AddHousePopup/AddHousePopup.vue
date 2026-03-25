<template>
  <div class="popup-overlay" @click="$emit('close')"></div>
  <div class="popup">
    <div class="popup-header">
      <div class="popup-title">🏠 เพิ่มบ้านใหม่</div>
      <button class="popup-close" @click="$emit('close')">&times;</button>
    </div>

    <div class="popup-section">
      <div class="section-label">ไอคอน</div>
      <div class="emoji-grid">
        <button 
          v-for="emoji in emojis" 
          :key="emoji"
          class="emoji-btn"
          :class="{ selected: selectedEmoji === emoji }"
          @click="selectedEmoji = emoji"
        >
          {{ emoji }}
        </button>
      </div>
    </div>

    <div class="popup-section">
      <label class="field-label">ชื่อบ้าน *</label>
      <input 
        v-model="houseName" 
        type="text" 
        class="modal-input"
        placeholder="เช่น บ้านหลังใหญ่"
      >
    </div>

    <div class="popup-section">
      <label class="field-label">ที่อยู่ *</label>
      <input 
        v-model="address" 
        type="text" 
        class="modal-input"
        placeholder="เช่น 123 ถนนสุขุมวิท กรุงเทพฯ"
      >
    </div>

    <p class="popup-error">{{ errorMessage }}</p>

    <div class="popup-actions">
      <button class="modal-btn-cancel" @click="$emit('close')">ยกเลิก</button>
      <button class="modal-btn-primary" @click="handleAdd">เพิ่มบ้าน</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emojis = ['🏠', '🏡', '🏢', '🏣', '🏤', '🏥', '🏦', '🏨', '🏩', '🏪', '🏫', '🏬', '🏭', '🏯', '🏰']

const selectedEmoji = ref('🏠')
const houseName = ref('')
const address = ref('')
const errorMessage = ref('')

const emit = defineEmits(['close', 'add'])

const handleAdd = () => {
  errorMessage.value = ''
  
  if (!houseName.value.trim()) {
    errorMessage.value = 'กรุณากรอกชื่อบ้าน'
    return
  }
  
  if (!address.value.trim()) {
    errorMessage.value = 'กรุณากรอกที่อยู่'
    return
  }
  
  emit('add', {
    house_name: houseName.value.trim(),
    address: address.value.trim(),
    emoji: selectedEmoji.value
  })
  
  // Reset form
  houseName.value = ''
  address.value = ''
  selectedEmoji.value = '🏠'
}
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.popup {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
  z-index: 1001;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.popup-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
}

.popup-close {
  background: none;
  border: none;
  color: var(--text2);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.popup-section {
  margin-bottom: 16px;
}

.section-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 8px;
}

.field-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 6px;
}

.emoji-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.emoji-btn {
  font-size: 20px;
  background: var(--surface2);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  width: 36px;
  height: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.emoji-btn.selected {
  border-color: var(--accent);
  background: var(--accent-dim);
}

.popup-error {
  font-size: 12px;
  color: var(--danger);
  min-height: 16px;
  margin: 8px 0;
}

.popup-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
</style>
