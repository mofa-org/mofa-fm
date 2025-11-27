<template>
  <div class="ai-script-studio">
    <div class="container">
      <h1 class="page-title">AI 脚本创作</h1>

      <!-- 会话列表视图 -->
      <div v-if="!currentSession" class="session-list-view">
        <div class="actions">
          <button @click="createNewSession" class="mofa-btn mofa-btn-primary">
            创建新会话
          </button>
        </div>

        <div v-if="loading" class="loading-state">加载中...</div>

        <div v-else-if="sessions.length === 0" class="empty-state">
          <p>还没有创作会话</p>
          <p class="hint">点击上方按钮开始创作你的第一个播客脚本</p>
        </div>

        <div v-else class="sessions-grid">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-card mofa-card"
            @click="loadSession(session.id)"
          >
            <div class="session-header">
              <h3 class="session-title">{{ session.title }}</h3>
              <button class="delete-button" @click.stop="confirmDeleteSession(session.id)">
                删除
              </button>
            </div>
            <div class="session-meta">
              <span>{{ formatDate(session.created_at) }}</span>
              <span>{{ session.chat_history?.length || 0 }} 条对话</span>
              <span>{{ session.uploaded_files_count || 0 }} 个文件</span>
            </div>
            <div v-if="session.current_script" class="session-preview">
              {{ session.current_script?.substring(0, 100) || '' }}...
            </div>
          </div>
        </div>

        <div class="generation-section mofa-card">
          <div class="section-header">
            <h2>生成记录</h2>
            <button class="mofa-btn mofa-btn-sm" @click="loadGenerationQueue">
              刷新
            </button>
          </div>
          <!-- 筛选控件已隐藏，显示所有任务 -->
          <div v-if="queueLoading" class="loading-state small">加载中...</div>
          <div v-else-if="generationQueue.length === 0" class="empty-state small">
            <p>暂无生成任务</p>
            <p class="hint">在会话中点击“生成播客”即可创建新的任务</p>
          </div>
          <div v-else class="generation-list">
            <div
              v-for="episode in generationQueue"
              :key="episode.id"
              class="generation-item"
              @click="openGenerationItem(episode)"
            >
              <div class="generation-info">
                <div class="generation-title">{{ episode.title }}</div>
                <div class="generation-meta">
                  <span>{{ episode.show?.title || '未关联节目' }}</span>
                  <span>提交于 {{ formatTime(episode.created_at) }}</span>
                </div>
              </div>
              <div class="generation-actions">
                <span :class="statusClass(episode.status)">{{ formatStatus(episode.status) }}</span>
                <button
                  v-if="canCancelEpisode(episode)"
                  class="queue-action queue-action-cancel"
                  @click.stop="cancelGeneration(episode)"
                >
                  取消
                </button>
                <button
                  v-else-if="canDeleteEpisode(episode)"
                  class="queue-action"
                  @click.stop="deleteGeneration(episode)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 创作工作区 -->
      <div v-else class="studio-workspace">
        <div class="workspace-header">
          <div class="header-left">
            <button @click="backToList" class="mofa-btn">
              返回列表
            </button>
            <div class="title-block">
              <h2 class="workspace-title">{{ currentSession.title }}</h2>
              <div v-if="sessionMeta" class="workspace-meta">
                <span class="meta-item">
                  <span class="label">关联节目：</span>{{ sessionMeta.showTitle }}
                </span>
                <span class="meta-item">
                  <span class="label">对话：</span>{{ sessionMeta.messageCount.toLocaleString('zh-CN') }} 条
                </span>
                <span class="meta-item">
                  <span class="label">文件：</span>{{ sessionMeta.fileCount.toLocaleString('zh-CN') }} 个
                </span>
                <span class="meta-item">
                  <span class="label">更新：</span>{{ sessionMeta.updatedAt ? formatTime(sessionMeta.updatedAt) : '刚刚' }}
                </span>
              </div>
            </div>
          </div>
          <div class="workspace-actions">
            <button
              class="mofa-btn delete-session-btn"
              @click="confirmDeleteSession(currentSession.id)"
              :disabled="generating"
            >
              删除会话
            </button>
            <button
              v-if="currentSession.current_script"
              @click="openGenerateDialog"
              class="mofa-btn mofa-btn-success"
              :disabled="generating"
            >
              {{ generating ? '生成中...' : '生成播客' }}
            </button>
          </div>
        </div>

        <div class="workspace-content">
          <!-- 左侧：对话区 -->
          <div class="chat-panel mofa-card">
            <div class="panel-header">
              <h3>对话</h3>
              <div class="header-actions">
                <TrendingPanel @select-trending="handleTrendingSelect" />
                <button @click="showUploadDialog = true" class="mofa-btn mofa-btn-sm">
                  上传参考文件
                </button>
              </div>
            </div>

            <!-- 参考文件列表 -->
            <div v-if="currentSession.uploaded_files?.length > 0" class="reference-files">
              <div class="files-header">参考文件 ({{ currentSession.uploaded_files.length }})</div>
              <div class="files-list">
                <div
                  v-for="file in currentSession.uploaded_files"
                  :key="file.id"
                  class="file-item"
                >
                  <span class="file-name">{{ file.original_filename }}</span>
                  <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                  <button @click="deleteFile(file.id)" class="btn-delete">删除</button>
                </div>
              </div>
            </div>

            <!-- 对话消息 -->
            <div ref="chatMessages" class="chat-messages">
              <div v-if="!currentSession.chat_history || currentSession.chat_history.length === 0" class="chat-welcome">
                <p>开始与 AI 对话，创作你的播客脚本</p>
                <ul>
                  <li>告诉我你想要创作什么主题的播客</li>
                  <li>上传参考文件（支持 txt/pdf/md/docx）</li>
                  <li>让我帮你生成或修改脚本</li>
                </ul>
              </div>

              <div
                v-for="(msg, index) in currentSession.chat_history"
                :key="index"
                class="message"
                :class="[
                  msg.role,
                  { typing: msg.typing, system: msg.system, pending: msg.pending }
                ]"
              >
                <div class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
                <div class="message-content">
                  <div v-if="msg.typing" class="thinking-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                  <div v-else class="message-text" v-html="formatMessage(msg.content)"></div>
                  <div v-if="!msg.typing && msg.timestamp" class="message-time">
                    {{ formatTime(msg.timestamp) }}
                  </div>
                  <div v-if="msg.pending && !msg.typing" class="message-status">等待 AI 回复...</div>
                </div>
              </div>
            </div>

            <!-- 输入框 -->
            <div class="chat-input">
              <textarea
                v-model="userMessage"
                @keydown.ctrl.enter="sendMessage"
                placeholder="输入你的想法... (Ctrl+Enter 发送)"
                rows="3"
              ></textarea>
              <button
                @click="sendMessage"
                class="mofa-btn mofa-btn-primary"
                :disabled="!userMessage.trim() || aiThinking"
              >
                {{ aiThinking ? 'AI 回复中...' : '发送' }}
              </button>
            </div>
          </div>

          <!-- 右侧：脚本预览 -->
          <div class="script-panel mofa-card">
            <div class="panel-header">
              <h3>脚本预览</h3>
              <div class="panel-actions">
                <button
                  v-if="currentSession.current_script && !isEditingScript"
                  @click="startEditScript"
                  class="mofa-btn mofa-btn-sm"
                >
                  编辑
                </button>
                <button
                  v-if="isEditingScript"
                  @click="saveScriptEdit"
                  class="mofa-btn mofa-btn-sm mofa-btn-success"
                >
                  保存
                </button>
                <button
                  v-if="isEditingScript"
                  @click="cancelScriptEdit"
                  class="mofa-btn mofa-btn-sm"
                >
                  取消
                </button>
                <button
                  v-if="currentSession.current_script && !isEditingScript"
                  @click="copyScript"
                  class="mofa-btn mofa-btn-sm"
                >
                  复制
                </button>
              </div>
            </div>

            <div v-if="scriptMeta" class="script-meta">
              <span class="meta-item">
                <span class="label">字数：</span>{{ scriptMeta.words.toLocaleString('zh-CN') }}
              </span>
              <span class="meta-item">
                <span class="label">字符：</span>{{ scriptMeta.characters.toLocaleString('zh-CN') }}
              </span>
              <span class="meta-item">
                <span class="label">更新：</span>{{ scriptMeta.lastUpdated ? formatTime(scriptMeta.lastUpdated) : '刚刚' }}
              </span>
            </div>

            <div class="script-content">
              <div v-if="!currentSession.current_script" class="script-empty">
                <p>还没有生成脚本</p>
                <p class="hint">在左侧与 AI 对话，让它帮你创作脚本</p>
              </div>
              <textarea
                v-else-if="isEditingScript"
                v-model="editableScript"
                class="script-editor"
                placeholder="在这里编辑脚本..."
              ></textarea>
              <pre v-else class="script-text">{{ currentSession.current_script }}</pre>
            </div>

            <div v-if="currentSession.script_versions?.length > 1" class="script-versions">
              <div class="versions-header">历史版本 ({{ currentSession.script_versions.length }})</div>
              <div class="versions-list">
                <button
                  v-for="(version, index) in currentSession.script_versions.slice().reverse()"
                  :key="index"
                  @click="viewVersion(version)"
                  class="version-item"
                >
                  版本 {{ currentSession.script_versions.length - index }} - {{ formatTime(version.created_at) }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 上传文件对话框 -->
      <div v-if="showUploadDialog" class="modal-overlay" @click.self="showUploadDialog = false">
        <div class="modal-content mofa-card">
          <div class="modal-header">
            <h3>上传参考文件</h3>
            <button @click="showUploadDialog = false" class="btn-close">×</button>
          </div>
          <div class="modal-body">
            <p>支持格式：txt, pdf, md, docx（最大 10MB）</p>
            <input
              ref="fileInput"
              type="file"
              @change="handleFileSelect"
              accept=".txt,.pdf,.md,.docx"
              class="file-input"
            />
            <div v-if="uploadProgress > 0" class="upload-progress">
              <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
              <span>{{ uploadProgress }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成播客对话框 -->
      <div v-if="showGenerateDialog" class="modal-overlay" @click.self="closeGenerateDialog">
        <div class="modal-content mofa-card">
          <div class="modal-header">
            <h3>生成播客单集</h3>
            <button @click="closeGenerateDialog" class="btn-close">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>播客标题</label>
              <input
                v-model="generateTitle"
                type="text"
                placeholder="请输入生成的播客标题"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>关联节目</label>
              <select v-model="generateShowId" class="form-select">
                <option :value="null">请选择节目</option>
                <option v-for="show in availableShows" :key="show.id" :value="show.id">
                  {{ show.title }}
                </option>
              </select>
            </div>
            <p v-if="availableShows.length === 0" class="hint">暂无可用节目，请先到节目管理中创建节目。</p>
            <p v-if="generateError" class="error-message">{{ generateError }}</p>
          </div>
          <div class="modal-footer">
            <button @click="closeGenerateDialog" class="mofa-btn">取消</button>
            <button
              @click="confirmGeneratePodcast"
              class="mofa-btn mofa-btn-success"
              :disabled="generating || !generateTitle.trim() || !generateShowId"
            >
              {{ generating ? '提交中...' : '生成' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 新建会话对话框 -->
      <div v-if="showNewSessionDialog" class="modal-overlay" @click.self="showNewSessionDialog = false">
        <div class="modal-content mofa-card">
          <div class="modal-header">
            <h3>新建脚本创作会话</h3>
            <button @click="showNewSessionDialog = false" class="btn-close">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>会话标题</label>
              <input
                v-model="newSessionTitle"
                type="text"
                placeholder="例如：第一期 - 人工智能简介"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>关联节目（可选）</label>
              <select v-model="newSessionShowId" class="form-select">
                <option :value="null">不关联</option>
                <option v-for="show in myShows" :key="show.id" :value="show.id">
                  {{ show.title }}
                </option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="showNewSessionDialog = false" class="mofa-btn">取消</button>
            <button @click="confirmCreateSession" class="mofa-btn mofa-btn-primary" :disabled="!newSessionTitle.trim()">
              创建
            </button>
          </div>
        </div>
      </div>

      <!-- 历史版本查看对话框 -->
      <div v-if="showVersionDialog && viewingVersion" class="modal-overlay" @click.self="showVersionDialog = false">
        <div class="modal-content mofa-card version-modal">
          <div class="modal-header">
            <h3>脚本版本 {{ viewingVersion.version }}</h3>
            <button @click="showVersionDialog = false" class="btn-close">×</button>
          </div>
          <div class="modal-body">
            <div class="version-meta">
              <span>创建时间：{{ formatTime(viewingVersion.timestamp) }}</span>
              <span>字数：{{ viewingVersion.script?.length || 0 }}</span>
            </div>
            <div class="version-script-content">
              <pre class="script-text">{{ viewingVersion.script }}</pre>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="showVersionDialog = false" class="mofa-btn">关闭</button>
            <button @click="restoreVersion(viewingVersion)" class="mofa-btn mofa-btn-primary">
              恢复此版本
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import podcastsAPI from '@/api/podcasts'
import { ElMessage, ElMessageBox } from 'element-plus'
import TrendingPanel from '@/components/creator/TrendingPanel.vue'

const router = useRouter()

// 状态
const loading = ref(false)
const sessions = ref([])
const currentSession = ref(null)
const myShows = ref([])
const generationQueue = ref([])
const queueLoading = ref(false)
const queueFilters = ref([]) // 空数组表示显示所有状态的任务

// 聊天相关
const userMessage = ref('')
const aiThinking = ref(false)
const chatMessages = ref(null)

// 脚本编辑相关
const isEditingScript = ref(false)
const editableScript = ref('')

const sessionMeta = computed(() => {
  const session = currentSession.value
  if (!session) return null

  return {
    showTitle: session.show?.title || '未关联节目',
    messageCount: session.chat_history?.length || 0,
    fileCount: session.uploaded_files_count ?? session.uploaded_files?.length ?? 0,
    updatedAt: session.updated_at
  }
})

const scriptMeta = computed(() => {
  const session = currentSession.value
  if (!session?.current_script) return null

  const plain = session.current_script.trim()
  const wordCount = plain ? plain.replace(/\s+/g, ' ').split(' ').length : 0

  return {
    characters: plain.length,
    words: wordCount,
    lastUpdated: session.updated_at
  }
})

const availableShows = computed(() => {
  const shows = Array.isArray(myShows.value) ? [...myShows.value] : []
  const currentShow = currentSession.value?.show
  if (currentShow && !shows.some(show => show.id === currentShow.id)) {
    shows.push(currentShow)
  }
  return shows
})

const generationStatusOptions = [
  { code: 'processing', label: '生成中' },
  { code: 'failed', label: '失败' },
  { code: 'published', label: '已完成' }
]

// 上传相关
const showUploadDialog = ref(false)
const uploadProgress = ref(0)
const fileInput = ref(null)

// 生成播客
const generating = ref(false)
const showGenerateDialog = ref(false)
const generateTitle = ref('')
const generateShowId = ref(null)
const generateError = ref('')

// 新建会话
const showNewSessionDialog = ref(false)
const newSessionTitle = ref('')
const newSessionShowId = ref(null)

// 历史版本查看
const showVersionDialog = ref(false)
const viewingVersion = ref(null)

// 加载会话列表
async function loadSessions() {
  loading.value = true
  try {
    const data = await podcastsAPI.getScriptSessions()
    // 兼容分页和非分页两种响应格式
    sessions.value = Array.isArray(data) ? data : (data.results || [])
  } catch (error) {
    console.error('加载会话失败:', error)
    ElMessage.error('加载会话失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function loadGenerationQueue() {
  queueLoading.value = true
  try {
    const params = queueFilters.value.length ? { status: queueFilters.value.join(',') } : {}
    const data = await podcastsAPI.getGenerationQueue(params)
    const list = Array.isArray(data) ? data : (data.results || [])
    if (queueFilters.value.includes('published')) {
      generationQueue.value = list.filter(episode => {
        if (episode.status !== 'published') return true
        const desc = episode.description || ''
        const filePath = episode.audio_file || ''
        return desc.includes('AI Generated Podcast') || filePath.includes('generated_')
      })
    } else {
      generationQueue.value = list
    }
  } catch (error) {
    console.error('加载生成记录失败:', error)
  } finally {
    queueLoading.value = false
  }
}

// 加载我的节目
async function loadMyShows() {
  try {
    const data = await podcastsAPI.getMyShows()
    myShows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (error) {
    console.error('加载节目失败:', error)
  }
}

// 创建新会话
function createNewSession() {
  newSessionTitle.value = ''
  newSessionShowId.value = null
  showNewSessionDialog.value = true
}

async function confirmCreateSession() {
  if (!newSessionTitle.value.trim()) return

  try {
    const session = await podcastsAPI.createScriptSession({
      title: newSessionTitle.value,
      show_id: newSessionShowId.value
    })

    // 确保有基本字段
    if (!session.chat_history) session.chat_history = []
    if (!session.uploaded_files) session.uploaded_files = []

    showNewSessionDialog.value = false
    currentSession.value = session
    await nextTick()
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建会话失败，请稍后重试')
  }
}

// 加载会话
async function loadSession(sessionId) {
  try {
    const session = await podcastsAPI.getScriptSession(sessionId)
    currentSession.value = session
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载会话失败:', error)
    ElMessage.error('加载会话失败，请稍后重试')
  }
}

// 返回列表
function backToList() {
  currentSession.value = null
  loadSessions()
  loadGenerationQueue()
}

// 删除会话
async function confirmDeleteSession(sessionId) {
  if (!sessionId) return

  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？删除后无法恢复。',
      '删除会话',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )

    await podcastsAPI.deleteScriptSession(sessionId)

    if (currentSession.value?.id === sessionId) {
      currentSession.value = null
    }

    await loadSessions()
    await loadGenerationQueue()
    ElMessage.success('会话已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败，请稍后重试')
    }
  }
}

function canCancelEpisode(episode) {
  return episode?.status === 'processing'
}

function canDeleteEpisode(episode) {
  return episode?.status === 'failed'
}

function openGenerationItem(episode) {
  if (!episode?.show?.slug) {
    ElMessage.warning('暂时无法跳转，缺少节目信息')
    return
  }
  router.push({ name: 'manage-show', params: { slug: episode.show.slug }, query: { highlightEpisode: episode.slug } })
}

async function cancelGeneration(episode) {
  if (!episode?.id) return
  try {
    await ElMessageBox.confirm('确定要取消该生成任务吗？', '取消生成', {
      type: 'warning',
      confirmButtonText: '取消任务',
      cancelButtonText: '暂不'
    })
  } catch {
    return
  }

  try {
    await podcastsAPI.deleteEpisode(episode.id)
    await loadGenerationQueue()
  } catch (error) {
    console.error('取消生成任务失败:', error)
    ElMessage.error('取消失败，请稍后再试')
  }
}

async function deleteGeneration(episode) {
  if (!episode?.id) return
  try {
    await ElMessageBox.confirm('确认删除这条记录？', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  try {
    await podcastsAPI.deleteEpisode(episode.id)
    await loadGenerationQueue()
  } catch (error) {
    console.error('删除记录失败:', error)
    ElMessage.error('删除失败，请稍后再试')
  }
}

function toggleQueueFilter(status) {
  if (!status) return
  const index = queueFilters.value.indexOf(status)
  if (index >= 0) {
    queueFilters.value.splice(index, 1)
  } else {
    queueFilters.value.push(status)
  }
  if (queueFilters.value.length === 0) {
    queueFilters.value.push(status)
  }
  loadGenerationQueue()
}

// 处理热搜选择
function handleTrendingSelect({ item, source }) {
  if (!currentSession.value?.id) {
    ElMessage.warning('请先创建或选择一个会话')
    return
  }

  // 自动填充到输入框
  const prompt = `帮我基于"${item.title}"这个热门话题创作一个播客脚本。请先搜索获取最新信息。`
  userMessage.value = prompt

  ElMessage.success(`已选择来自 ${source} 的话题`)

  // 可选：自动滚动到输入框
  nextTick(() => {
    const textarea = document.querySelector('.chat-input textarea')
    if (textarea) {
      textarea.focus()
    }
  })
}

// 发送消息
async function sendMessage() {
  if (!userMessage.value.trim() || aiThinking.value) return

  if (!currentSession.value?.id) {
    ElMessage.error('会话未正确初始化，请刷新页面重试')
    return
  }

  const message = userMessage.value.trim()
  userMessage.value = ''
  aiThinking.value = true

  if (!currentSession.value.chat_history) {
    currentSession.value.chat_history = []
  }

  const localMessage = {
    role: 'user',
    content: message,
    timestamp: new Date().toISOString(),
    pending: true
  }

  currentSession.value.chat_history.push(localMessage)
  const typingMessage = {
    role: 'assistant',
    content: '正在思考...',
    timestamp: null,
    typing: true
  }
  currentSession.value.chat_history.push(typingMessage)
  await nextTick()
  scrollToBottom()

  try {
    // 检测是否可能需要搜索
    const searchKeywords = ['今天', '昨天', '最近', '最新', '沪指', '股市', '新闻', '热点', '搜索', '查询']
    const needsSearch = searchKeywords.some(keyword => message.includes(keyword))

    if (needsSearch) {
      typingMessage.content = '正在搜索实时信息...'
      await nextTick()
    }

    const data = await podcastsAPI.chatWithAI(currentSession.value.id, message)
    localMessage.pending = false

    if (data.has_script_update) {
      currentSession.value.chat_history = currentSession.value.chat_history.filter(
        msg => msg !== typingMessage
      )
      await loadSession(currentSession.value.id)
    } else {
      const aiReply = data.message || 'AI 已完成处理'
      typingMessage.typing = false
      typingMessage.content = aiReply
      typingMessage.timestamp = new Date().toISOString()
      if (data.script && (!currentSession.value.current_script || data.script !== currentSession.value.current_script)) {
        currentSession.value.current_script = data.script
      }
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    localMessage.pending = false
    typingMessage.typing = false

    let errorMsg = '发送失败，请重试'

    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorMsg = '请求超时，可能是搜索耗时较长。请刷新页面重新加载试试看。'
    } else if (error.response?.status === 500) {
      errorMsg = '服务器错误，请刷新页面重新加载试试看。'
    } else if (error.response?.status === 504) {
      errorMsg = '网关超时，可能是搜索耗时较长。请刷新页面重新加载试试看。'
    } else {
      errorMsg = error.response?.data?.error || error.response?.data?.detail || '发送失败，请刷新页面重新加载试试看。'
    }

    typingMessage.content = errorMsg
    typingMessage.timestamp = new Date().toISOString()
  } finally {
    aiThinking.value = false
  }
}

// 上传文件
function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return

  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  uploadFile(file)
}

async function uploadFile(file) {
  uploadProgress.value = 0

  try {
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    await podcastsAPI.uploadReference(currentSession.value.id, file)

    clearInterval(progressInterval)
    uploadProgress.value = 100

    setTimeout(() => {
      showUploadDialog.value = false
      uploadProgress.value = 0
      loadSession(currentSession.value.id)
    }, 500)
  } catch (error) {
    console.error('上传文件失败:', error)
    ElMessage.error('上传文件失败，请稍后重试')
    uploadProgress.value = 0
  }
}

// 删除文件
async function deleteFile(fileId) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个文件吗？',
      '删除文件',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )

    await podcastsAPI.deleteReference(currentSession.value.id, fileId)
    loadSession(currentSession.value.id)
    ElMessage.success('文件已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error)
      ElMessage.error('删除文件失败，请稍后重试')
    }
  }
}

// 生成播客
function openGenerateDialog() {
  if (!currentSession.value?.current_script) {
    ElMessage.warning('请先生成脚本')
    return
  }

  showGenerateDialog.value = true
  generateError.value = ''
  generateTitle.value = currentSession.value.title || ''
  const currentShowId = currentSession.value.show?.id ?? null
  generateShowId.value = currentShowId ?? (availableShows.value[0]?.id ?? null)
}

function closeGenerateDialog() {
  if (generating.value) return
  showGenerateDialog.value = false
  generateError.value = ''
}

async function confirmGeneratePodcast() {
  if (generating.value) return

  if (!generateTitle.value.trim()) {
    generateError.value = '请输入播客标题'
    return
  }

  const showId = Number(generateShowId.value ?? currentSession.value.show?.id ?? 0)
  if (!Number.isInteger(showId) || showId <= 0) {
    generateError.value = '请选择要生成的节目'
    return
  }

  generating.value = true
  generateError.value = ''

  try {
    await podcastsAPI.generateEpisode({
      show_id: showId,
      title: generateTitle.value.trim(),
      description: '由 AI 脚本创作工具生成',
      script: currentSession.value.current_script
    })

    showGenerateDialog.value = false
    ElMessage.success({
      message: '播客生成任务已提交！',
      description: '请稍后在右侧"生成记录"中查看进度',
      duration: 3000
    })
    await loadGenerationQueue()
  } catch (error) {
    console.error('生成播客失败:', error)
    generateError.value = error.response?.data?.error || error.response?.data?.detail || '请稍后重试'
  } finally {
    generating.value = false
  }
}

// 复制脚本
function copyScript() {
  navigator.clipboard.writeText(currentSession.value.current_script)
  ElMessage.success('脚本已复制到剪贴板')
}

// 开始编辑脚本
function startEditScript() {
  editableScript.value = currentSession.value.current_script
  isEditingScript.value = true
}

// 取消编辑脚本
function cancelScriptEdit() {
  isEditingScript.value = false
  editableScript.value = ''
}

// 保存脚本编辑
function saveScriptEdit() {
  if (!editableScript.value.trim()) {
    ElMessage.warning('脚本内容不能为空')
    return
  }

  currentSession.value.current_script = editableScript.value
  isEditingScript.value = false
  ElMessage.success('脚本已更新，可以直接生成播客')
}

// 查看历史版本
function viewVersion(version) {
  viewingVersion.value = version
  showVersionDialog.value = true
}

// 恢复历史版本
async function restoreVersion(version) {
  try {
    await ElMessageBox.confirm(
      '确定要恢复到这个版本吗？当前脚本将被覆盖。',
      '恢复版本',
      {
        type: 'warning',
        confirmButtonText: '恢复',
        cancelButtonText: '取消'
      }
    )

    currentSession.value.current_script = version.script
    showVersionDialog.value = false
    ElMessage.success('已恢复到版本 ' + version.version)
  } catch (error) {
    // 用户取消
  }
}

// 工具函数
function scrollToBottom() {
  if (chatMessages.value) {
    chatMessages.value.scrollTop = chatMessages.value.scrollHeight
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

function formatTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatStatus(status) {
  const map = {
    draft: '草稿',
    processing: '生成中',
    published: '已发布',
    failed: '生成失败'
  }
  return map[status] || status
}

function statusClass(status) {
  return {
    draft: 'status-badge status-draft',
    processing: 'status-badge status-processing',
    published: 'status-badge status-published',
    failed: 'status-badge status-failed'
  }[status] || 'status-badge'
}

function formatMessage(content) {
  if (!content) return ''

  // 1. 先移除最外层的 markdown 代码块标记（如果有）
  let text = content.trim()
  if (text.startsWith('```markdown') || text.startsWith('```')) {
    text = text.replace(/^```(?:markdown)?\n?/, '')
    text = text.replace(/\n?```$/, '')
  }

  // 2. 处理标题
  text = text.replace(/^### (.*?)$/gm, '<h3>$1</h3>')
  text = text.replace(/^## (.*?)$/gm, '<h2>$1</h2>')
  text = text.replace(/^# (.*?)$/gm, '<h1>$1</h1>')

  // 3. 处理粗体
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // 4. 处理斜体
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')

  // 5. 处理【角色】标记
  text = text.replace(/【(.*?)】/g, '<strong class="role-tag">【$1】</strong>')

  // 6. 最后处理换行
  text = text.replace(/\n\n/g, '<br><br>')
  text = text.replace(/\n/g, '<br>')

  return text
}

onMounted(() => {
  loadSessions()
  loadMyShows()
  loadGenerationQueue()
})
</script>

<style scoped>
.ai-script-studio {
  padding: var(--spacing-xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-xl);
}

/* 会话列表 */
.actions {
  margin-bottom: var(--spacing-xl);
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.session-card {
  cursor: pointer;
  transition: var(--transition);
}

.session-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.session-title {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  margin: 0;
}

.session-meta {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
}

.delete-button {
  background: none;
  border: none;
  color: var(--color-warning-dark);
  font-size: var(--font-sm);
  cursor: pointer;
  padding: 0;
  white-space: nowrap;
}

.delete-button:hover {
  color: var(--color-warning);
  text-decoration: underline;
}

.session-preview {
  color: var(--color-text-secondary);
  font-size: var(--font-sm);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
}

.generation-section {
  margin-top: var(--spacing-xl);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.section-header h2 {
  margin: 0;
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
}

.generation-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.queue-filters {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.queue-filter {
  padding: 6px 14px;
  border-radius: 999px;
  border: var(--border-width) solid var(--border-color-light);
  background: var(--color-white);
  font-size: var(--font-xs);
  cursor: pointer;
  transition: var(--transition);
}

.queue-filter.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(255, 81, 59, 0.1);
}

.generation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border: var(--border-width) solid var(--border-color-light);
  border-radius: var(--radius-default);
  background: var(--color-white);
  cursor: pointer;
  transition: var(--transition);
}

.generation-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.generation-item:hover {
  border-color: var(--color-primary);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.generation-title {
  font-weight: var(--font-semibold);
  font-size: var(--font-base);
}

.generation-meta {
  display: flex;
  gap: var(--spacing-md);
  color: var(--color-text-tertiary);
  font-size: var(--font-xs);
}

.generation-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: var(--font-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
}

.status-processing {
  background: rgba(255, 197, 62, 0.12);
  color: var(--color-warning-dark);
}

.status-failed {
  background: rgba(255, 81, 59, 0.12);
  color: var(--color-primary);
}

.status-published {
  background: rgba(109, 202, 208, 0.15);
  color: var(--color-success-dark);
}

.status-draft {
  background: rgba(113, 128, 150, 0.12);
  color: var(--color-text-tertiary);
}

.queue-action {
  border: var(--border-width) solid var(--border-color);
  background: transparent;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: var(--font-xs);
  cursor: pointer;
  transition: var(--transition);
}

.queue-action:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.queue-action-cancel {
  border-color: var(--color-warning-dark);
  color: var(--color-warning-dark);
}

.queue-action-cancel:hover {
  background: rgba(255, 197, 62, 0.12);
}

/* 工作区 */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.header-left {
  display: flex;
  gap: var(--spacing-lg);
  align-items: flex-start;
}

.title-block {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.workspace-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
}

.workspace-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.meta-item .label {
  color: var(--color-text-secondary);
}

.workspace-actions {
  display: flex;
  gap: var(--spacing-md);
}

.delete-session-btn {
  border: 1px solid var(--color-warning-dark);
  color: var(--color-warning-dark);
  background: transparent;
}

.delete-session-btn:hover {
  background: var(--color-warning);
  color: var(--color-white);
}

.delete-session-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.workspace-content {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(300px, 1fr);
  gap: var(--spacing-lg);
  align-items: stretch;
  overflow-x: hidden;
}

/* 面板通用样式 */
.chat-panel,
.script-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 280px);
  min-height: 600px;
  max-width: 100%;
  overflow-x: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-xs);
  border-bottom: var(--border-width) solid var(--border-color);
}

.panel-header h3 {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

/* 参考文件 */
.reference-files {
  margin-bottom: var(--spacing-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
}

.files-header {
  font-weight: var(--font-semibold);
  margin-bottom: var(--spacing-xs);
  font-size: 11px;
  color: var(--color-text-secondary);
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  background: var(--color-white);
  padding: 4px var(--spacing-xs);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: var(--color-text-tertiary);
  font-size: 10px;
}

.btn-delete {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: 11px;
  cursor: pointer;
  padding: 0;
}

/* 对话消息 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  margin-bottom: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-xs);
}

.chat-welcome {
  color: var(--color-text-tertiary);
  padding: var(--spacing-md);
  font-size: var(--font-sm);
}

.chat-welcome ul {
  margin-top: var(--spacing-xs);
  padding-left: var(--spacing-md);
}

.message {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
  align-items: flex-start;
  width: 100%;
}

.message-role {
  font-size: var(--font-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  min-width: 32px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
  background: var(--color-bg);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  word-wrap: break-word;
  overflow-wrap: break-word;
  font-size: var(--font-sm);
  line-height: 1.5;
}

.message.assistant .message-content {
  background: var(--color-bg-secondary);
  border-left: 3px solid var(--color-primary);
}

.message.typing .message-content {
  display: flex;
  align-items: center;
}

.message.system .message-content {
  background: rgba(109, 202, 208, 0.15);
  border-left: none;
  color: var(--color-text-secondary);
}

.message-text {
  line-height: 1.5;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.message-text * {
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-text h1,
.message-text h2,
.message-text h3 {
  margin: var(--spacing-xs) 0;
  font-weight: var(--font-bold);
  line-height: 1.3;
}

.message-text h1 {
  font-size: var(--font-lg);
}

.message-text h2 {
  font-size: var(--font-base);
}

.message-text h3 {
  font-size: var(--font-sm);
}

.message-text .role-tag {
  color: var(--color-primary);
  font-weight: var(--font-bold);
  font-size: inherit;
}

.message-time {
  font-size: 10px;
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-xs);
}

.message-status {
  margin-top: var(--spacing-xs);
  font-size: 10px;
  color: var(--color-primary);
}

.thinking-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
}

.thinking-indicator .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-tertiary);
  animation: thinking-bounce 1.2s infinite ease-in-out;
}

.thinking-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 输入框 */
.chat-input {
  display: flex;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs);
  background: var(--color-bg);
  border-radius: var(--radius-default);
}

.chat-input textarea {
  flex: 1;
  padding: var(--spacing-xs);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: var(--font-sm);
  resize: vertical;
  min-height: 60px;
  overflow-x: hidden;
  line-height: 1.5;
}

.chat-input textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.chat-input textarea:disabled {
  background: var(--color-bg);
  color: var(--color-text-tertiary);
}

/* 脚本预览 */
.script-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.script-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: var(--spacing-sm);
}

.script-empty {
  color: var(--color-text-tertiary);
  padding: var(--spacing-md);
  font-size: var(--font-sm);
}

.hint {
  color: var(--color-text-placeholder);
  font-size: 11px;
  margin-top: var(--spacing-xs);
}

.error-message {
  margin-top: var(--spacing-xs);
  color: var(--color-primary);
  font-size: var(--font-sm);
}

.script-text {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  line-height: 1.6;
  padding: var(--spacing-sm);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  margin: 0;
  font-size: 13px;
}

.script-editor {
  width: 100%;
  height: 100%;
  min-height: 400px;
  padding: var(--spacing-md);
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-primary);
  background: var(--color-white);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-default);
  resize: vertical;
  outline: none;
  transition: var(--transition-fast);
  box-shadow: inset 2px 2px 0 rgba(0, 0, 0, 0.05);
}

.script-editor:focus {
  border-color: var(--color-primary);
  box-shadow: inset 2px 2px 0 rgba(0, 0, 0, 0.05), 0 0 0 3px rgba(255, 81, 59, 0.1);
}

.panel-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.script-versions {
  border-top: var(--border-width) solid var(--border-color);
  padding-top: var(--spacing-md);
}

.versions-header {
  font-weight: var(--font-semibold);
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-sm);
}

.versions-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  max-height: 150px;
  overflow-y: auto;
}

.version-item {
  background: var(--color-bg);
  border: none;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  text-align: left;
  cursor: pointer;
  font-size: var(--font-xs);
  transition: var(--transition);
}

.version-item:hover {
  background: var(--color-bg-secondary);
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 500px;
}

.modal-content.version-modal {
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-content.version-modal .modal-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.version-meta {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: var(--border-width) solid var(--border-color);
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
}

.version-script-content {
  flex: 1;
  overflow-y: auto;
  background: var(--color-bg);
  border-radius: var(--radius-default);
  padding: var(--spacing-md);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: var(--border-width) solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-lg);
}

.btn-close {
  background: none;
  border: none;
  font-size: var(--font-2xl);
  cursor: pointer;
  color: var(--color-text-tertiary);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  margin-bottom: var(--spacing-md);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: var(--border-width) solid var(--border-color);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: var(--font-semibold);
  font-size: var(--font-sm);
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--spacing-sm);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-default);
  font-size: var(--font-base);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.file-input {
  width: 100%;
  padding: var(--spacing-sm);
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-default);
  cursor: pointer;
}

.upload-progress {
  margin-top: var(--spacing-md);
  background: var(--color-bg);
  border-radius: var(--radius-default);
  height: 32px;
  position: relative;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--gradient-bar);
  transition: width 0.3s;
}

.upload-progress span {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: var(--font-semibold);
  font-size: var(--font-sm);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--spacing-3xl);
  color: var(--color-text-tertiary);
}

.loading-state.small,
.empty-state.small {
  padding: var(--spacing-xl);
}

.code-block {
  background: var(--color-bg-secondary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  margin: var(--spacing-xs) 0;
  font-family: 'Courier New', monospace;
  font-size: var(--font-sm);
  max-width: 100%;
}

@media (max-width: 1360px) {
  .workspace-content {
    grid-template-columns: 1fr;
  }

  .chat-panel,
  .script-panel {
    height: auto;
    min-height: auto;
  }
}

@media (max-width: 1024px) {
  .workspace-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-lg);
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
  }

  .workspace-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
