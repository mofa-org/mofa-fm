<template>
  <div class="comment-item-container">
    <div class="comment-content mofa-card" :class="{ 'is-reply': isReply }">
      <!-- 用户信息和元数据 -->
      <div class="comment-header">
        <div class="user-info">
          <el-avatar :size="32" :src="comment.user.avatar_url || '/default_avatar.png'" />
          <span class="username">{{ comment.user.username }}</span>
          <span class="time">{{ formatDate(comment.created_at) }}</span>
        </div>

        <div class="actions">
          <el-button 
            v-if="!isReplying" 
            link 
            type="primary" 
            size="small" 
            @click="toggleReply"
          >
            回复
          </el-button>
          <el-popconfirm
            v-if="isSelf"
            title="确定要删除这条评论吗？"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @confirm="handleDelete"
          >
            <template #reference>
              <el-button link type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <!-- 评论内容 -->
      <div class="comment-body">
        <p>{{ comment.text }}</p>
      </div>

      <!-- 回复框 -->
      <div v-if="isReplying" class="reply-form">
        <el-input
          v-model="replyText"
          type="textarea"
          :rows="2"
          placeholder="写下你的回复..."
          ref="replyInput"
        />
        <div class="reply-actions">
          <el-button size="small" @click="cancelReply">取消</el-button>
          <el-button 
            type="primary" 
            size="small" 
            :loading="submitting" 
            @click="submitReply"
            :disabled="!replyText.trim()"
          >
            发送
          </el-button>
        </div>
      </div>

      <!-- 折叠/展开按钮 -->
      <div 
        v-if="hasChildren" 
        class="collapse-toggle" 
        @click="toggleExpand"
      >
        <el-icon :class="{ 'is-expanded': isExpanded }"><ArrowRight /></el-icon>
        <span>{{ isExpanded ? '收起' : `展开 ${comment.children.length} 条回复` }}</span>
      </div>
    </div>

    <!-- 递归渲染子评论 -->
    <div v-if="hasChildren && isExpanded" class="nested-comments">
      <CommentItem
        v-for="child in comment.children"
        :key="child.id"
        :comment="child"
        :episode-id="episodeId"
        :depth="depth + 1"
        is-reply
        @reply-success="$emit('reply-success')"
        @delete-success="$emit('delete-success')"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'

// 递归组件名称
defineOptions({
  name: 'CommentItem'
})

const props = defineProps({
  comment: {
    type: Object,
    required: true
  },
  episodeId: {
    type: [Number, String],
    required: true
  },
  isReply: {
    type: Boolean,
    default: false
  },
  depth: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['reply-success', 'delete-success'])

const authStore = useAuthStore()
const isReplying = ref(false)
const replyText = ref('')
const submitting = ref(false)
const isExpanded = ref(true)
const replyInput = ref(null)

const isSelf = computed(() => {
  return authStore.isAuthenticated && authStore.user.id === props.comment.user.id
})

const hasChildren = computed(() => {
  return props.comment.children && props.comment.children.length > 0
})

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function toggleReply() {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  isReplying.value = !isReplying.value
  if (isReplying.value) {
    nextTick(() => {
      replyInput.value?.focus()
    })
  }
}

function cancelReply() {
  isReplying.value = false
  replyText.value = ''
}

async function submitReply() {
  if (!replyText.value.trim()) return

  submitting.value = true
  try {
    await api.interactions.createComment({
      episode: props.episodeId,
      text: replyText.value,
      parent: props.comment.id
    })
    ElMessage.success('回复成功')
    isReplying.value = false
    replyText.value = ''
    // 自动展开以显示新回复
    isExpanded.value = true
    emit('reply-success')
  } catch (error) {
    console.error('回复失败', error)
    ElMessage.error('回复失败，请重试')
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  try {
    await api.interactions.deleteComment(props.comment.id)
    ElMessage.success('删除成功')
    emit('delete-success')
  } catch (error) {
    console.error('删除失败', error)
    ElMessage.error('删除失败，请重试')
  }
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
.comment-item-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.comment-content {
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  box-shadow: none;
  background-color: var(--color-bg);
}

.comment-content.is-reply {
  background-color: var(--color-bg-secondary);
  border-left: 3px solid var(--color-border);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.username {
  font-weight: var(--font-semibold);
  font-size: var(--font-sm);
  color: var(--color-text-primary);
}

.time {
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
}

.comment-body {
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  font-size: var(--font-base);
  word-break: break-word;
}

.actions {
  display: flex;
  gap: var(--spacing-xs);
}

.reply-form {
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-color-light);
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-xs);
}

.nested-comments {
  margin-left: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  border-left: 2px solid var(--border-color-light);
  padding-left: var(--spacing-md);
}

.collapse-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
  cursor: pointer;
  user-select: none;
  margin-top: var(--spacing-xs);
  width: fit-content;
}

.collapse-toggle:hover {
  color: var(--color-primary);
}

.collapse-toggle .el-icon {
  transition: transform 0.2s;
}

.collapse-toggle .el-icon.is-expanded {
  transform: rotate(90deg);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .nested-comments {
    margin-left: var(--spacing-md);
    padding-left: var(--spacing-sm);
  }
}
</style>
