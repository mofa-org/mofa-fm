<template>
  <div class="debate-viewer">
    <div class="container">
      <!-- 加载中 -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 生成中 -->
      <div v-else-if="episode && episode.status === 'processing'" class="processing-state">
        <div class="debate-content">
          <!-- 头部信息 -->
          <div class="debate-header">
            <div class="header-left">
              <button class="mofa-btn" @click="$router.back()">返回</button>
            </div>
            <div class="header-center">
              <h1 class="debate-title">{{ episode.title }}</h1>
              <div class="debate-meta">
                <span class="mode-badge" :class="`mode-${episode.mode}`">
                  <el-icon><ChatDotRound v-if="episode.mode === 'debate'" /><ChatLineSquare v-else /></el-icon>
                  {{ episode.mode === 'debate' ? '辩论' : '会议' }}
                </span>
                <span class="generating-badge">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  生成中... {{ dialogue.length }} 条
                </span>
              </div>
            </div>
            <div class="header-right"></div>
          </div>

          <!-- 对话区域 -->
          <div class="dialogue-container">
            <div v-if="dialogue.length === 0" class="loading-placeholder inline-placeholder">
              <h2>辩论已开始</h2>
              <p>正在生成开场陈词...</p>
            </div>

            <div
              v-for="(entry, index) in dialogue"
              :key="index"
              :class="['dialogue-entry', `participant-${entry.participant}`]"
            >
              <div class="entry-avatar" :style="avatarStyle(entry.participant)">
                {{ getParticipantIcon(entry.participant) }}
              </div>
              <div class="entry-card">
                <div class="entry-header">
                  <span class="entry-role">{{ getParticipantRole(entry.participant) }}</span>
                  <span class="entry-time">{{ formatTime(entry.timestamp) }}</span>
                </div>
                <div class="entry-content">
                  {{ entry.content }}
                </div>
              </div>
            </div>

            <!-- 生成中提示 -->
            <div class="generating-indicator">
              <div class="spinner-small"></div>
              <p>{{ dialogue.length > 0 ? 'AI正在继续生成...' : 'AI正在组织第一轮观点...' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成失败 -->
      <div v-else-if="episode && episode.status === 'failed'" class="error-state">
        <h2>生成失败</h2>
        <p>对话生成过程中出现错误，请重试</p>
        <button class="mofa-btn mofa-btn-primary" @click="$router.push({ name: 'create-debate' })">
          重新创建
        </button>
      </div>

      <!-- 辩论内容 -->
      <div v-else-if="episode && dialogue.length > 0" class="debate-content">
        <!-- 头部信息 -->
        <div class="debate-header">
          <div class="header-left">
            <button class="mofa-btn" @click="$router.back()">返回</button>
          </div>
          <div class="header-center">
            <h1 class="debate-title">{{ episode.title }}</h1>
            <div class="debate-meta">
              <span class="mode-badge" :class="`mode-${episode.mode}`">
                <el-icon><ChatDotRound v-if="episode.mode === 'debate'" /><ChatLineSquare v-else /></el-icon>
                {{ episode.mode === 'debate' ? '辩论' : '会议' }}
              </span>
              <span>{{ dialogue.length }} 条对话</span>
              <span>{{ formatDate(episode.created_at) }}</span>
            </div>
          </div>
          <div class="header-right">
            <!-- 生成音频按钮 -->
            <button
              v-if="canGenerateAudio"
              class="mofa-btn mofa-btn-success"
              @click="handleGenerateAudio"
              :disabled="audioGenerating"
            >
              <el-icon><Microphone /></el-icon>
              {{ audioGenerating ? '生成中...' : '生成音频' }}
            </button>
            <span v-else-if="episode.audio_file" class="audio-badge">
              <el-icon><Check /></el-icon>
              已有音频
            </span>
          </div>
        </div>

        <!-- 对话区域 -->
        <div class="dialogue-container">
          <div
            v-for="(entry, index) in dialogue"
            :key="index"
            :class="['dialogue-entry', `participant-${entry.participant}`]"
          >
            <div class="entry-avatar" :style="avatarStyle(entry.participant)">
              {{ getParticipantIcon(entry.participant) }}
            </div>
            <div class="entry-card">
              <div class="entry-header">
                <span class="entry-role">{{ getParticipantRole(entry.participant) }}</span>
                <span class="entry-time">{{ formatTime(entry.timestamp) }}</span>
              </div>
              <div class="entry-content">
                {{ entry.content }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误 -->
      <div v-else class="error-state">
        <h2>加载失败</h2>
        <p>{{ error || '无法加载对话内容' }}</p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  ChatLineSquare,
  Loading,
  Microphone,
  Check
} from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()

const episode = ref(null)
const loading = ref(true)
const error = ref('')
let eventSource = null

// Audio generation
const audioGenerating = ref(false)

const dialogue = ref([])  // Changed from computed to ref for real-time updates

const participantConfig = computed(() => {
  if (!episode.value?.participants_config) return {}
  return episode.value.participants_config.reduce((acc, p) => {
    acc[p.id] = p
    return acc
  }, {})
})

const canGenerateAudio = computed(() => {
  return episode.value?.status === 'published' &&
         dialogue.value.length > 0 &&
         !episode.value?.audio_file
})

onMounted(async () => {
  await loadEpisode()

  // 如果正在生成，启动SSE流式传输
  if (episode.value?.status === 'processing') {
    startStreaming()
  }
})

onUnmounted(() => {
  stopStreaming()
})

async function loadEpisode() {
  try {
    loading.value = true
    episode.value = await api.podcasts.getEpisodeById(route.params.episodeId)
    dialogue.value = episode.value?.dialogue || []
  } catch (err) {
    console.error('Failed to load episode:', err)
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleGenerateAudio() {
  if (!episode.value?.id || audioGenerating.value) return

  try {
    audioGenerating.value = true

    await api.podcasts.generateDebateAudio(episode.value.id)
    episode.value.status = 'processing'

    startStreaming()
  } catch (err) {
    console.error('Failed to generate audio:', err)
    error.value = err.response?.data?.error || '音频生成失败'
  } finally {
    audioGenerating.value = false
  }
}

function startStreaming() {
  // 关闭已存在的连接
  stopStreaming()

  const episodeId = route.params.episodeId
  const token = localStorage.getItem('access_token')
  if (!token) {
    error.value = '登录已过期，请重新登录'
    return
  }

  // 构建SSE URL（需要在URL中传递token，因为EventSource不支持自定义headers）
  // 使用相对路径，让nginx代理处理
  const streamUrl = `/api/podcasts/episodes/${episodeId}/stream/?token=${token}`

  eventSource = new EventSource(streamUrl)

  // 监听对话事件
  eventSource.addEventListener('dialogue', (e) => {
    try {
      const entry = JSON.parse(e.data)
      mergeOrAppendDialogue(entry)
      scrollToBottom()
    } catch (err) {
      console.error('Failed to parse dialogue event:', err)
    }
  })

  // 监听增量更新（同一条发言逐字增长）
  eventSource.addEventListener('delta', (e) => {
    try {
      const delta = JSON.parse(e.data)
      applyDelta(delta)
      scrollToBottom()
    } catch (err) {
      console.error('Failed to parse delta event:', err)
    }
  })

  // 监听完成事件
  eventSource.addEventListener('complete', (e) => {
    try {
      const data = JSON.parse(e.data)
      console.log('Debate generation complete:', data)
      episode.value.status = 'published'
      audioGenerating.value = false
      stopStreaming()
    } catch (err) {
      console.error('Failed to parse complete event:', err)
    }
  })

  // 监听业务错误事件（非连接错误）
  eventSource.addEventListener('stream_error', (e) => {
    console.error('SSE error:', e)
    try {
      const errorData = JSON.parse(e.data)
      error.value = errorData.error || '生成失败'
      if (episode.value) {
        episode.value.status = 'failed'
      }
    } catch (err) {
      console.error('Failed to parse stream_error event:', err)
    }
    audioGenerating.value = false
    stopStreaming()
  })

  // 监听连接错误
  eventSource.onerror = (e) => {
    console.error('EventSource connection error:', e)
    // 浏览器会自动重连，这里不主动关闭。
    // 若已被服务器关闭，则清理实例。
    if (eventSource?.readyState === EventSource.CLOSED) {
      stopStreaming()
    }
  }
}

function mergeOrAppendDialogue(entry) {
  if (!entry) return
  const lastIndex = dialogue.value.length - 1
  const last = dialogue.value[lastIndex]
  if (last && last.participant === entry.participant) {
    const lastContent = last.content || ''
    const nextContent = entry.content || ''
    if (
      nextContent === lastContent ||
      nextContent.startsWith(lastContent) ||
      lastContent.startsWith(nextContent)
    ) {
      dialogue.value[lastIndex] = { ...last, ...entry }
      return
    }
  }
  dialogue.value.push(entry)
}

function applyDelta(delta) {
  if (!delta) return

  const index = Number.isInteger(delta.index) ? delta.index : dialogue.value.length - 1
  if (index >= 0 && index < dialogue.value.length) {
    const current = dialogue.value[index]
    dialogue.value[index] = {
      ...current,
      participant: delta.participant || current.participant,
      content: delta.content || current.content,
      timestamp: delta.timestamp || current.timestamp
    }
    return
  }

  if (delta.participant || delta.content) {
    dialogue.value.push({
      participant: delta.participant || 'judge',
      content: delta.content || '',
      timestamp: delta.timestamp || new Date().toISOString()
    })
  }
}

function scrollToBottom() {
  setTimeout(() => {
    const container = document.querySelector('.dialogue-container')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }, 100)
}

function stopStreaming() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

function getParticipantRole(participantId) {
  return participantConfig.value[participantId]?.role || participantId
}

function getParticipantIcon(participantId) {
  const icons = {
    judge: '主',
    tutor: '师',
    llm1: '正',
    llm2: '反',
    student1: '甲',
    student2: '乙'
  }
  return icons[participantId] || participantId.charAt(0).toUpperCase()
}

function avatarStyle(participantId) {
  const colors = {
    judge: 'var(--color-warning)',      // 黄色
    tutor: 'var(--color-warning)',      // 黄色
    llm1: 'var(--color-primary)',       // 红橙
    llm2: 'var(--color-success)',       // 青蓝
    student1: 'var(--color-primary)',   // 红橙
    student2: 'var(--color-success)'    // 青蓝
  }
  return {
    background: colors[participantId] || 'var(--color-gray)'
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.debate-viewer {
  padding: 2rem 0;
  min-height: 100vh;
}

/* 加载和错误状态 */
.loading-state,
.loading-placeholder,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
}

.loading-placeholder.inline-placeholder {
  padding: 1rem 0 0.5rem;
}

.loading-placeholder.inline-placeholder h2 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.loading-placeholder.inline-placeholder p {
  margin: 0;
  color: var(--color-text-secondary);
}

.spinner {
  width: 50px;
  height: 50px;
  margin: 0 auto 1rem;
  border: 4px solid var(--color-light-gray);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 生成中状态 */
.processing-state {
  width: 100%;
}

.generating-badge {
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg,
    rgba(255, 198, 62, 0.15),
    rgba(255, 198, 62, 0.25)
  );
  color: var(--color-warning-dark);
  font-weight: var(--font-semibold);
  animation: pulse 2s ease-in-out infinite;
  border: 2px solid rgba(255, 198, 62, 0.3);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(0.98);
  }
}

.generating-indicator {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
  background: linear-gradient(135deg,
    rgba(255, 198, 62, 0.03),
    rgba(109, 202, 208, 0.03)
  );
  border-radius: var(--radius-default);
  margin-top: var(--spacing-lg);
}

.generating-indicator .spinner-small {
  margin: 0 auto 0.5rem;
}

/* 头部 */
.debate-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  background: var(--color-white);
  border-radius: var(--radius-default);
  box-shadow: var(--shadow-sm);
  border: var(--border-width-thin) solid var(--border-color-light);
  margin-bottom: var(--spacing-2xl);
  transition: var(--transition);
}

.debate-header:hover {
  box-shadow: var(--shadow-md);
}

.header-center {
  flex: 1;
  text-align: center;
  margin: 0 2rem;
}

.debate-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.debate-meta {
  display: flex;
  gap: 1rem;
  justify-content: center;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.mode-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 500;
}

.mode-badge.mode-debate {
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.1),
    rgba(255, 81, 59, 0.2)
  );
  color: var(--color-primary);
}

.mode-badge.mode-conference {
  background: linear-gradient(135deg,
    rgba(109, 202, 208, 0.1),
    rgba(109, 202, 208, 0.2)
  );
  color: var(--color-success);
}

/* 对话容器 */
.dialogue-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 1rem;
}

.dialogue-entry {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.entry-avatar {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.entry-card {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-white);
  border-radius: var(--radius-default);
  box-shadow: var(--shadow-sm);
  border: var(--border-width-thin) solid var(--border-color-light);
  transition: var(--transition-fast);
}

.entry-card:hover {
  transform: translateY(-2px) translateX(2px);
  box-shadow: var(--shadow-md);
}

.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.entry-role {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 0.95rem;
}

.entry-time {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
}

.entry-content {
  color: var(--color-text-secondary);
  line-height: 1.7;
  font-size: 1rem;
}

/* 不同参与者的样式变化 */
.participant-judge .entry-card,
.participant-tutor .entry-card {
  border-left: 4px solid var(--color-warning);
}

.participant-llm1 .entry-card,
.participant-student1 .entry-card {
  border-left: 4px solid var(--color-primary);
}

.participant-llm2 .entry-card,
.participant-student2 .entry-card {
  border-left: 4px solid var(--color-success);
}

/* 音频徽章 */
.audio-badge {
  padding: 0.5rem 1rem;
  background: var(--gradient-success);
  color: var(--color-white);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  border: var(--border-width-thin) solid var(--color-success);
  box-shadow: var(--shadow-sm);
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-soft-lg);
  border: var(--border-width) solid var(--border-color);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-light-gray);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--color-light-gray);
  color: var(--color-text-primary);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.loading-shows {
  text-align: center;
  padding: 2rem 0;
}

.spinner-small {
  width: 32px;
  height: 32px;
  margin: 0 auto 0.5rem;
  border: 3px solid var(--color-light-gray);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.shows-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.show-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: var(--border-width-thin) solid var(--border-color-light);
  border-radius: var(--radius-default);
  cursor: pointer;
  transition: var(--transition-fast);
  background: var(--color-white);
}

.show-item:hover {
  border-color: var(--color-primary-light);
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.03),
    rgba(255, 81, 59, 0.08)
  );
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.show-item.selected {
  border-color: var(--color-primary);
  border-width: var(--border-width);
  background: var(--gradient-primary);
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.08),
    rgba(253, 85, 63, 0.15)
  );
  box-shadow: var(--shadow-md);
}

.show-cover {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: var(--color-light-gray);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.show-info {
  flex: 1;
  min-width: 0;
}

.show-title {
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.show-meta {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.check-icon {
  width: 28px;
  height: 28px;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.no-shows {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-secondary);
}

.no-shows .hint {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-top: 0.5rem;
}

.modal-error {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
  font-size: 0.875rem;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--color-light-gray);
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

/* 响应式 */
@media (max-width: 768px) {
  .debate-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-left,
  .header-center,
  .header-right {
    width: 100%;
    margin: 0;
  }

  .header-center {
    text-align: left;
  }

  .debate-meta {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .dialogue-entry {
    gap: 0.75rem;
  }

  .entry-avatar {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }

  .entry-card {
    padding: 0.875rem 1rem;
  }

  .modal-content {
    max-width: 100%;
    max-height: 90vh;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-footer .mofa-btn {
    width: 100%;
  }
}
</style>
