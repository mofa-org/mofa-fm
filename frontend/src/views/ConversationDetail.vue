<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div>
            <el-button size="small" @click="$router.back()">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
            <span class="card-title" style="margin-left: 16px">{{ conversation.title }}</span>
          </div>
          <el-button type="primary" @click="handleFinalize" :loading="finalizing">
            确认生成脚本
          </el-button>
        </div>
      </template>

      <div class="chat-container">
        <div class="messages-area" ref="messagesAreaRef">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']"
          >
            <div class="message-avatar">
              <el-icon v-if="message.role === 'user'"><User /></el-icon>
              <el-icon v-else><Robot /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>

          <div v-if="sending" class="message assistant-message">
            <div class="message-avatar">
              <el-icon><Robot /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text typing">AI 正在思考...</div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            placeholder="输入你的需求，例如：请加一段关于开源模型的讨论..."
            @keydown.ctrl.enter="handleSend"
          />
          <div class="input-actions">
            <span class="input-tip">Ctrl + Enter 发送</span>
            <el-button type="primary" @click="handleSend" :loading="sending">
              发送
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { conversationAPI } from '@/api'

const route = useRoute()
const router = useRouter()
const messagesAreaRef = ref()
const sending = ref(false)
const finalizing = ref(false)
const userInput = ref('')

const conversation = ref({
  id: '',
  title: '',
  topic: '',
  style: '',
  status: 'active',
  message_count: 0
})

const messages = ref([])

const formatTime = (dateStr) => {
  return new Date(dateStr).toLocaleTimeString('zh-CN')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesAreaRef.value) {
      messagesAreaRef.value.scrollTop = messagesAreaRef.value.scrollHeight
    }
  })
}

const fetchConversation = async () => {
  try {
    const data = await conversationAPI.get(route.params.id)
    conversation.value = data
    messages.value = data.messages || []
    scrollToBottom()
  } catch (error) {
    ElMessage.error('加载对话失败')
  }
}

const handleSend = async () => {
  if (!userInput.value.trim()) return

  const content = userInput.value
  userInput.value = ''

  // 添加用户消息
  messages.value.push({
    id: Date.now() + '_user',
    role: 'user',
    content,
    created_at: new Date().toISOString()
  })
  scrollToBottom()

  sending.value = true
  try {
    const aiMessage = await conversationAPI.sendMessage(route.params.id, { content })

    messages.value.push(aiMessage)
    scrollToBottom()
  } catch (error) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

const handleFinalize = async () => {
  finalizing.value = true
  try {
    const result = await conversationAPI.finalize(route.params.id)
    ElMessage.success('脚本已生成')
    router.push(`/scripts`)
  } catch (error) {
    ElMessage.error('生成失败')
  } finally {
    finalizing.value = false
  }
}

onMounted(() => {
  fetchConversation()
})
</script>

<style scoped>
.card-header {
  padding: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-container {
  height: calc(100vh - 250px);
  display: flex;
  flex-direction: column;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.assistant-message .message-avatar {
  background: #67c23a;
}

.message-content {
  max-width: 70%;
}

.message-text {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  word-wrap: break-word;
}

.user-message .message-text {
  background: #409eff;
  color: white;
}

.message-text.typing {
  font-style: italic;
  color: #909399;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: right;
}

.user-message .message-time {
  text-align: left;
}

.input-area {
  margin-top: 16px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-tip {
  font-size: 12px;
  color: #909399;
}
</style>
