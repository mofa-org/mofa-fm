<template>
  <div v-if="visible" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content mofa-card voice-config-modal">
      <div class="modal-header">
        <h3>声线配置</h3>
        <button @click="handleClose" class="btn-close">×</button>
      </div>
      
      <div class="modal-body">
        <p class="intro-text">为脚本中的角色分配 TTS 音色。角色将从脚本中的【角色名】标签自动识别。</p>
        
        <div v-if="roles.length === 0" class="empty-roles">
          <p>未在脚本中检测到角色标签。</p>
          <p class="hint">请确保脚本包含如 【主持人】、【嘉宾】 等格式的标签。</p>
        </div>

        <div v-else class="role-list">
          <div v-for="role in roles" :key="role" class="role-item">
            <div class="role-name">{{ role }}</div>
            <div class="voice-select-wrapper">
              <el-select 
                v-model="localConfig[role]" 
                placeholder="选择音色" 
                size="large"
                class="voice-select"
              >
                <el-option
                  v-for="voice in availableVoices"
                  :key="voice.id"
                  :label="voice.name"
                  :value="voice.id"
                >
                  <span class="voice-option">
                    <span class="voice-name">{{ voice.name }}</span>
                    <span class="voice-desc">{{ voice.description }}</span>
                  </span>
                </el-option>
              </el-select>
            </div>
            
            <button 
              class="btn-play-sample" 
              @click="playSample(localConfig[role])"
              title="试听（暂未实现）"
              disabled
            >
              <el-icon><VideoPlay /></el-icon>
            </button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="handleClose" class="mofa-btn">取消</button>
        <button 
          @click="handleSave" 
          class="mofa-btn mofa-btn-primary"
          :disabled="loading"
        >
          {{ loading ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { VideoPlay } from '@element-plus/icons-vue'
import { getTTSVoices } from '@/api/podcasts'

const props = defineProps({
  visible: Boolean,
  scriptContent: {
    type: String,
    default: ''
  },
  initialConfig: {
    type: Object,
    default: () => ({})
  },
  loading: Boolean
})

const emit = defineEmits(['update:visible', 'save', 'close'])

const localConfig = ref({})
const availableVoices = ref([])
const voicesLoading = ref(false)

// 加载 MiniMax TTS 音色列表
async function loadVoices() {
  voicesLoading.value = true
  try {
    const res = await getTTSVoices({ language: 'zh' })
    if (res.data && res.data.voices) {
      // 只显示中文音色
      availableVoices.value = res.data.voices
        .filter(v => v.language === 'zh' || v.language === 'other')
        .map(v => ({
          id: v.voice_id,
          name: v.voice_name,
          description: v.description || ''
        }))
    }
  } catch (e) {
    console.error('加载音色失败:', e)
    // 使用默认音色作为 fallback
    availableVoices.value = [
      { id: 'Chinese (Mandarin)_News_Anchor', name: '大牛（新闻主播）', description: '专业稳重' },
      { id: 'Chinese (Mandarin)_Gentleman', name: '一帆（绅士）', description: '温和有礼' },
      { id: 'Chinese (Mandarin)_Radio_Host', name: '博宇（电台主持人）', description: '亲切自然' },
      { id: 'Chinese (Mandarin)_Mature_Woman', name: '成熟女性', description: '成熟稳重' },
      { id: 'Chinese (Mandarin)_Warm_Girl', name: '温暖女孩', description: '温暖亲切' },
    ]
  } finally {
    voicesLoading.value = false
  }
}

onMounted(() => {
  loadVoices()
})

// 自动提取角色
const roles = computed(() => {
  if (!props.scriptContent) return []
  
  // 匹配 【角色名】 格式
  const regex = /【(.*?)】/g
  const matches = [...props.scriptContent.matchAll(regex)]
  // 提取并去重
  const uniqueRoles = [...new Set(matches.map(m => m[1]))]
  return uniqueRoles.filter(r => r.trim())
})

// 初始化配置
watch(() => props.visible, (newVal) => {
  if (newVal) {
    // 复制初始配置
    localConfig.value = { ...props.initialConfig }
    
    // 为新发现的角色设置默认值（如果未配置）
    roles.value.forEach((role, index) => {
      if (!localConfig.value[role]) {
        // 简单的默认分配策略
        const defaultVoice = availableVoices[index % availableVoices.length].id
        localConfig.value[role] = defaultVoice
      }
    })
  }
})

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

function handleSave() {
  emit('save', { ...localConfig.value })
}

function playSample(voiceId) {
  // TODO: 实现试听
  console.log('Play sample for', voiceId)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.voice-config-modal {
  /* Specific override if needed */
}

.modal-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  line-height: 1;
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.intro-text {
  color: var(--color-text-secondary);
  font-size: var(--font-sm);
  margin-bottom: var(--spacing-lg);
}

.empty-roles {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.role-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.role-name {
  font-weight: var(--font-bold);
  min-width: 80px;
  color: var(--color-text-primary);
}

.voice-select-wrapper {
  flex: 1;
}

.voice-select {
  width: 100%;
}

.voice-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.voice-desc {
  color: var(--color-text-tertiary);
  font-size: var(--font-xs);
}

.btn-play-sample {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: var(--font-lg);
  padding: var(--spacing-xs);
  display: flex;
  align-items: center;
  opacity: 0.5; /* Disabled appearance */
}

.btn-play-sample:not(:disabled) {
  opacity: 1;
}

.modal-footer {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

/* ElSelect custom styling fix */
:deep(.el-select .el-input__wrapper) {
  background-color: var(--color-bg-primary);
}
</style>
