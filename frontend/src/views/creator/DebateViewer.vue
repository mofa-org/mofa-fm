<template>
  <div class="debate-viewer">
    <div class="container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="episode" class="debate-shell">
        <div class="debate-header">
          <button class="mofa-btn" @click="$router.back()">返回</button>
          <div class="header-center">
            <h1 class="debate-title">{{ episode.title }}</h1>
            <div class="debate-meta">
              <span class="mode-badge" :class="`mode-${episode.mode}`">
                <el-icon><ChatDotRound v-if="episode.mode === 'debate'" /><ChatLineSquare v-else /></el-icon>
                {{ episode.mode === 'debate' ? '辩论' : '会议' }}
              </span>
              <span class="status-badge" :class="`status-${episode.status}`">
                <el-icon v-if="isGenerating" class="is-loading"><Loading /></el-icon>
                {{ statusText }}
              </span>
            </div>
          </div>
        </div>

        <div ref="chatPanelRef" class="chat-panel">
          <div
            v-for="(entry, index) in dialogue"
            :key="entry.timestamp ? `${entry.participant}-${entry.timestamp}` : index"
            :class="['chat-row', `participant-${entry.participant}`]"
          >
            <div class="entry-avatar" :style="avatarStyle(entry.participant)">
              {{ getParticipantIcon(entry.participant) }}
            </div>
            <div class="entry-bubble">
              <div class="entry-header">
                <span class="entry-role">{{ getParticipantRole(entry.participant) }}</span>
                <span class="entry-time">{{ formatTime(entry.timestamp) }}</span>
              </div>
              <div class="entry-content">
                {{ entry.content }}
                <span
                  v-if="activeStreamingIndex === index && isGenerating && entry.participant !== 'user'"
                  class="typing-cursor"
                >|</span>
              </div>
            </div>
          </div>

          <div v-if="dialogue.length === 0" class="empty-tip">
            <h3>辩论已开始</h3>
            <p>正在生成首轮发言...</p>
          </div>
        </div>

        <div class="composer">
          <textarea
            v-model="inputMessage"
            class="composer-input"
            placeholder="输入你的观点，按 Enter 发送（Shift+Enter 换行）"
            rows="2"
            :disabled="sending || !canInteract"
            @keydown.enter.exact.prevent="sendMessage"
          ></textarea>
          <button
            class="mofa-btn mofa-btn-primary"
            :disabled="!canSend"
            @click="sendMessage"
          >
            {{ sending ? '发送中...' : '发送' }}
          </button>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>

      <div v-else class="error-state">
        <h2>加载失败</h2>
        <p>{{ error || '无法加载辩论内容' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  ChatLineSquare,
  Loading
} from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()

const episode = ref(null)
const loading = ref(true)
const error = ref('')
const dialogue = ref([])
const inputMessage = ref('')
const sending = ref(false)
const activeStreamingIndex = ref(-1)
const chatPanelRef = ref(null)

// 消息ID集合，用于去重（防止消息被重复添加或覆盖）
const messageIds = ref(new Set())

let eventSource = null

// 生成唯一ID
function generateMessageId(entry) {
  if (!entry) return ''
  // 使用参与者+内容哈希+时间戳（取到秒）生成唯一ID
  const content = entry.content || ''
  const participant = entry.participant || ''
  const timestamp = entry.timestamp || ''
  // 取时间戳的前19位（到秒），忽略毫秒差异
  const tsPrefix = typeof timestamp === 'string' ? timestamp.slice(0, 19) : timestamp
  return `${participant}:${tsPrefix}:${content.slice(0, 50)}`
}

const participantConfig = computed(() => {
  if (!episode.value?.participants_config) return {}
  return episode.value.participants_config.reduce((acc, p) => {
    acc[p.id] = p
    return acc
  }, {})
})

const isGenerating = computed(() => episode.value?.status === 'processing')
const canInteract = computed(() => !!episode.value)
const canSend = computed(() => {
  return !!inputMessage.value.trim() && !sending.value && !!episode.value && canInteract.value
})

const statusText = computed(() => {
  if (!episode.value) return ''
  if (episode.value.status === 'processing') return 'AI正在辩论'
  if (episode.value.status === 'published') return '辩论中，可继续插话'
  if (episode.value.status === 'failed') return '生成失败'
  return episode.value.status
})

onMounted(async () => {
  await loadEpisode()
  if (episode.value?.status === 'processing') {
    startStreaming()
  }
  scrollToBottom()
})

onUnmounted(() => {
  stopStreaming()
})

async function loadEpisode() {
  try {
    loading.value = true
    const data = await api.podcasts.getEpisodeById(route.params.episodeId)
    episode.value = data
    dialogue.value = data?.dialogue || []
    // 初始化消息ID集合
    messageIds.value.clear()
    dialogue.value.forEach(entry => {
      messageIds.value.add(generateMessageId(entry))
      if (entry.participant === 'user' && entry.content) {
        messageIds.value.add(`user:${entry.content.slice(0, 50)}`)
      }
    })
  } catch (err) {
    console.error('Failed to load episode:', err)
    error.value = err.response?.data?.error || '加载失败'
  } finally {
    loading.value = false
  }
}

async function refreshEpisode() {
  const data = await api.podcasts.getEpisodeById(route.params.episodeId)
  episode.value = data
  // 合并服务器数据和本地数据，避免覆盖用户刚发送的消息
  const serverDialogue = data?.dialogue || []
  const localDialogue = dialogue.value || []

  // 如果本地有用户消息但服务器还没有，保留本地消息
  if (localDialogue.length > serverDialogue.length) {
    // 保留本地额外的消息（通常是刚发送的用户消息）
    dialogue.value = [...serverDialogue, ...localDialogue.slice(serverDialogue.length)]
  } else {
    dialogue.value = serverDialogue
  }
  scrollToBottom()
}

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message || !episode.value?.id || sending.value) return

  try {
    sending.value = true
    error.value = ''

    // 乐观更新：立即将用户消息添加到本地对话
    const clientId = `client-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    const userEntry = {
      participant: 'user',
      role: '我',
      content: message,
      timestamp: new Date().toISOString(),
      clientId  // 客户端唯一标识，用于去重
    }
    // 添加ID到集合，防止后续被覆盖
    messageIds.value.add(generateMessageId(userEntry))
    // 也添加一个基于内容的备用ID
    messageIds.value.add(`user:${message.slice(0, 50)}`)
    dialogue.value.push(userEntry)
    scrollToBottom()

    await api.podcasts.sendDebateMessage(episode.value.id, message)
    inputMessage.value = ''
    episode.value.status = 'processing'

    // 不立即刷新，让 SSE 流来更新对话，避免覆盖刚添加的用户消息
    if (!eventSource || eventSource.readyState === EventSource.CLOSED) {
      startStreaming()
    }
  } catch (err) {
    console.error('Failed to send debate message:', err)
    error.value = err.response?.data?.error || '发送失败'
  } finally {
    sending.value = false
  }
}

function startStreaming() {
  stopStreaming()

  const episodeId = route.params.episodeId
  const token = localStorage.getItem('access_token')
  if (!token) {
    error.value = '登录已过期，请重新登录'
    return
  }

  const streamUrl = `/api/podcasts/episodes/${episodeId}/stream/?token=${token}`
  eventSource = new EventSource(streamUrl)

  eventSource.addEventListener('dialogue', (e) => {
    try {
      const entry = JSON.parse(e.data)
      const index = mergeOrAppendDialogue(entry)
      if (entry.participant !== 'user') {
        activeStreamingIndex.value = index
      }
      scrollToBottom()
    } catch (err) {
      console.error('Failed to parse dialogue event:', err)
    }
  })

  eventSource.addEventListener('delta', (e) => {
    try {
      const delta = JSON.parse(e.data)
      applyDelta(delta)
      scrollToBottom()
    } catch (err) {
      console.error('Failed to parse delta event:', err)
    }
  })

  eventSource.addEventListener('complete', () => {
    if (episode.value) {
      episode.value.status = 'published'
    }
    activeStreamingIndex.value = -1
    stopStreaming()
  })

  eventSource.addEventListener('stream_error', (e) => {
    try {
      const payload = JSON.parse(e.data)
      error.value = payload.error || '生成失败'
    } catch (err) {
      error.value = '生成失败'
      console.error('Failed to parse stream_error event:', err)
    }
    if (episode.value) {
      episode.value.status = 'failed'
    }
    activeStreamingIndex.value = -1
    stopStreaming()
  })

  eventSource.onerror = () => {
    if (eventSource?.readyState === EventSource.CLOSED) {
      stopStreaming()
    }
  }
}

function stopStreaming() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

function mergeOrAppendDialogue(entry) {
  if (!entry) return dialogue.value.length - 1

  // 1. 检查是否有 clientId 匹配（精确匹配本地乐观添加的消息）
  if (entry.clientId) {
    const idxByClientId = dialogue.value.findIndex((item) => item.clientId === entry.clientId)
    if (idxByClientId >= 0) {
      dialogue.value[idxByClientId] = { ...dialogue.value[idxByClientId], ...entry }
      return idxByClientId
    }
  }

  // 2. 生成消息ID并检查是否已存在（防止完全重复的消息）
  const msgId = generateMessageId(entry)
  if (messageIds.value.has(msgId)) {
    const idx = dialogue.value.findIndex((item) => generateMessageId(item) === msgId)
    if (idx >= 0) {
      dialogue.value[idx] = { ...dialogue.value[idx], ...entry }
      return idx
    }
  }

  // 3. 特殊处理用户消息：检查内容是否匹配（防止乐观添加的消息和SSE推送的重复）
  if (entry.participant === 'user' && entry.content) {
    const contentPrefix = entry.content.slice(0, 50)
    const contentId = `user:${contentPrefix}`
    if (messageIds.value.has(contentId)) {
      // 已存在相同内容的用户消息，更新时间戳等信息
      const idx = dialogue.value.findIndex((item) =>
        item.participant === 'user' && item.content === entry.content
      )
      if (idx >= 0) {
        dialogue.value[idx] = { ...dialogue.value[idx], ...entry }
        return idx
      }
    }
  }

  // 4. 特殊处理：检查是否是同一参与者的流式更新（内容前缀匹配）
  const lastIndex = dialogue.value.length - 1
  const last = dialogue.value[lastIndex]
  if (last && last.participant === entry.participant && entry.participant !== 'user') {
    const lastContent = last.content || ''
    const nextContent = entry.content || ''
    // 只有当内容有明显包含关系时才合并（流式更新）
    if (nextContent.startsWith(lastContent) || lastContent.startsWith(nextContent)) {
      const clientId = last.clientId
      dialogue.value[lastIndex] = { ...last, ...entry }
      if (clientId) dialogue.value[lastIndex].clientId = clientId
      return lastIndex
    }
  }

  // 5. 新消息，追加
  messageIds.value.add(msgId)
  if (entry.participant === 'user' && entry.content) {
    messageIds.value.add(`user:${entry.content.slice(0, 50)}`)
  }
  dialogue.value.push(entry)
  return dialogue.value.length - 1
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
    activeStreamingIndex.value = index
  }
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatPanelRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

function getParticipantRole(participantId) {
  if (participantId === 'user') return '我'
  return participantConfig.value[participantId]?.role || participantId
}

function getParticipantIcon(participantId) {
  const icons = {
    user: '我',
    judge: '主',
    tutor: '师',
    llm1: '正',
    llm2: '反',
    student1: '甲',
    student2: '乙'
  }
  return icons[participantId] || participantId?.charAt(0)?.toUpperCase() || '?'
}

function avatarStyle(participantId) {
  const colors = {
    user: '#4f5b93',
    judge: 'var(--color-warning)',
    tutor: 'var(--color-warning)',
    llm1: 'var(--color-primary)',
    llm2: 'var(--color-success)',
    student1: 'var(--color-primary)',
    student2: 'var(--color-success)'
  }

  return {
    background: colors[participantId] || 'var(--color-gray)'
  }
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.debate-viewer {
  padding: 1.5rem 0;
  min-height: calc(100vh - 64px);
}

.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
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

.debate-shell {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.debate-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-radius: 12px;
  border: 1px solid var(--border-color-light);
  background: var(--color-white);
}

.header-center {
  flex: 1;
}

.debate-title {
  margin: 0 0 0.35rem;
  font-size: 1.2rem;
  color: var(--color-text-primary);
}

.debate-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.mode-badge,
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
}

.mode-debate {
  background: rgba(255, 81, 59, 0.12);
  color: var(--color-primary);
}

.mode-conference {
  background: rgba(109, 202, 208, 0.16);
  color: var(--color-success);
}

.status-processing {
  background: rgba(255, 198, 62, 0.18);
  color: #9a6e00;
}

.status-published {
  background: rgba(46, 204, 113, 0.14);
  color: #1f8d4a;
}

.status-failed {
  background: rgba(231, 76, 60, 0.14);
  color: #b83b2c;
}

.chat-panel {
  height: min(62vh, 640px);
  overflow-y: auto;
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--border-color-light);
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
}

.chat-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.95rem;
  align-items: flex-start;
}

.entry-avatar {
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
}

.entry-bubble {
  flex: 1;
  background: var(--color-white);
  border: 1px solid var(--border-color-light);
  border-radius: 12px;
  padding: 0.65rem 0.8rem;
}

.participant-user .entry-bubble {
  border-color: #a8b1d8;
  background: #f6f8ff;
}

.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.entry-role {
  font-weight: 700;
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.entry-time {
  color: var(--color-text-tertiary);
  font-size: 0.78rem;
}

.entry-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.typing-cursor {
  margin-left: 2px;
  animation: blink 0.9s steps(1) infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

.empty-tip {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 2rem 1rem;
}

.empty-tip h3 {
  margin: 0 0 0.35rem;
  color: var(--color-text-primary);
}

.composer {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  padding: 0.9rem;
  border: 1px solid var(--border-color-light);
  border-radius: 12px;
  background: var(--color-white);
}

.composer-input {
  flex: 1;
  resize: vertical;
  min-height: 48px;
  max-height: 180px;
  border: 1px solid var(--color-light-gray);
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
  font-family: inherit;
  font-size: 0.95rem;
}

.composer-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.error-message {
  color: #b83b2c;
  background: #fff2f0;
  border: 1px solid #ffc9c3;
  border-radius: 10px;
  padding: 0.7rem 0.8rem;
}

@media (max-width: 768px) {
  .debate-viewer {
    padding: 1rem 0;
  }

  .debate-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chat-panel {
    height: min(58vh, 520px);
  }

  .composer {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
