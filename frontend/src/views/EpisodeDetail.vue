<template>
  <div class="episode-detail-page" v-if="episode">
    <div class="container">
      <!-- 单集信息 -->
      <div class="episode-header mofa-card">
        <img :src="episode.cover_url" :alt="episode.title" class="episode-cover" />

        <div class="episode-info">
          <div class="title-row">
            <h1 class="episode-title">{{ episode.title }}</h1>
            <VisibilityBadge :visibility="effectiveVisibility" />
          </div>

          <router-link :to="`/shows/${episode.show.slug}`" class="show-name">
            {{ episode.show.title }}
          </router-link>

          <p class="episode-description">{{ episode.description }}</p>

          <div class="episode-meta">
            <span>{{ formatDuration(episode.duration) }}</span>
            <span>{{ episode.play_count }} 播放</span>
            <span>{{ episode.like_count }} 点赞</span>
            <span>{{ formatDate(episode.published_at) }}</span>
          </div>

          <div class="episode-actions">
            <el-button type="primary" size="large" @click="handlePlay">
              <el-icon><VideoPlay /></el-icon>
              播放
            </el-button>
            <el-button v-if="isAuthenticated" @click="handleLike">
              <el-icon><Star :style="episode.is_liked ? { color: '#ffc63e' } : {}" /></el-icon>
              {{ episode.is_liked ? '已点赞' : '点赞' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 脚本查看器 -->
      <div v-if="episode.script" class="script-section">
        <ScriptViewer
          :episode-id="episode.id"
          :script="episode.script"
          :is-creator="isCreator"
          @script-updated="handleScriptUpdated"
        />
      </div>

      <!-- 评论区 -->
      <div class="comments-section">
        <h2 class="section-title">评论 ({{ episode.comment_count }})</h2>

        <!-- 发表评论 -->
        <div v-if="isAuthenticated" class="comment-form mofa-card">
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="3"
            placeholder="发表评论..."
          />
          <el-button type="primary" @click="handleComment" :loading="commenting">
            发表
          </el-button>
        </div>

        <!-- 评论列表 -->
        <div class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item mofa-card">
            <div class="comment-user">
              <el-avatar :size="40" :src="comment.user.avatar_url" :icon="UserFilled" />
              <span class="username">{{ comment.user.username }}</span>
              <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
            </div>
            <p class="comment-text">{{ comment.text }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Star, UserFilled } from '@element-plus/icons-vue'
import VisibilityBadge from '@/components/common/VisibilityBadge.vue'
import ScriptViewer from '@/components/podcast/ScriptViewer.vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const episode = ref(null)
const comments = ref([])
const commentText = ref('')
const commenting = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)

const isCreator = computed(() => {
  if (!isAuthenticated.value || !episode.value) return false
  return episode.value.show.creator.id === authStore.user.id
})

const effectiveVisibility = computed(() => {
  if (!episode.value) return 'public'
  if (!episode.value.visibility || episode.value.visibility === 'inherit') {
    return episode.value.show?.visibility || 'public'
  }
  return episode.value.visibility
})

onMounted(async () => {
  const { showSlug, episodeSlug } = route.params
  episode.value = await api.podcasts.getEpisode(showSlug, episodeSlug)

  const data = await api.interactions.getComments(episode.value.id)
  comments.value = data.results || data
})

function handlePlay() {
  playerStore.play(episode.value)
}

async function handleLike() {
  try {
    const data = await api.interactions.toggleLike(episode.value.id)
    episode.value.is_liked = data.liked
    episode.value.like_count = data.like_count
  } catch (error) {
    // 错误已处理
  }
}

async function handleComment() {
  if (!commentText.value.trim()) return

  commenting.value = true
  try {
    await api.interactions.createComment({
      episode: episode.value.id,
      text: commentText.value
    })
    ElMessage.success('评论成功')
    commentText.value = ''

    // 重新加载评论
    const data = await api.interactions.getComments(episode.value.id)
    comments.value = data.results || data
    episode.value.comment_count++
  } finally {
    commenting.value = false
  }
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function handleScriptUpdated(updatedEpisode) {
  // 更新episode的script字段
  episode.value.script = updatedEpisode.script
}
</script>

<style scoped>
.episode-detail-page {
  padding: var(--spacing-xl) 0;
}

.episode-header {
  display: flex;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-2xl);
}

.episode-cover {
  width: 300px;
  height: 300px;
  object-fit: cover;
  border-radius: var(--radius-lg);
}

.episode-info {
  flex: 1;
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-sm);
}

.episode-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin: 0;
}

.show-name {
  font-size: var(--font-lg);
  color: var(--color-primary);
  display: block;
  margin-bottom: var(--spacing-md);
}

.episode-description {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
  line-height: var(--line-height-relaxed);
}

.episode-meta {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-tertiary);
}

.episode-actions {
  display: flex;
  gap: var(--spacing-md);
}

.script-section {
  margin-top: var(--spacing-2xl);
}

.comments-section {
  margin-top: var(--spacing-2xl);
}

.section-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
}

.comment-form {
  margin-bottom: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.comment-item {
  padding: var(--spacing-md);
}

.comment-user {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.username {
  font-weight: var(--font-semibold);
}

.comment-time {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.comment-text {
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}
</style>
