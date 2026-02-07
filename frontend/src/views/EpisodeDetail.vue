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
            <el-button
              v-if="isAuthenticated"
              :type="isFollowing ? 'success' : 'warning'"
              @click="handleFollow"
            >
              <el-icon><Bell /></el-icon>
              {{ isFollowing ? '已订阅' : '订阅此节目' }}
            </el-button>
            <el-button v-if="isAuthenticated" @click="handleLike">
              <el-icon><Star :style="episode.is_liked ? { color: '#ffc63e' } : {}" /></el-icon>
              {{ episode.is_liked ? '已点赞' : '点赞' }}
            </el-button>
            <el-button @click="openShareCard" :loading="shareLoading">
              <el-icon><Share /></el-icon>
              分享卡片
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

      <el-dialog
        v-model="shareDialogVisible"
        title="分享卡片"
        width="min(540px, 92vw)"
      >
        <div class="share-panel">
          <img
            v-if="sharePosterDataUrl"
            :src="sharePosterDataUrl"
            alt="分享海报"
            class="share-poster"
          />
          <p v-if="shareError" class="share-error">{{ shareError }}</p>
          <p v-else-if="shareCardData" class="share-text">{{ shareCardData.share_text }}</p>
          <div class="share-actions">
            <el-button @click="copyShareText" :disabled="!shareCardData">复制文案</el-button>
            <el-button type="primary" @click="downloadSharePoster" :disabled="!sharePosterDataUrl">
              下载卡片
            </el-button>
          </div>
        </div>
        <canvas ref="shareCanvasRef" width="1080" height="1920" class="hidden-canvas"></canvas>
      </el-dialog>

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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { VideoPlay, Star, UserFilled, Bell, Share } from '@element-plus/icons-vue'
import VisibilityBadge from '@/components/common/VisibilityBadge.vue'
import ScriptViewer from '@/components/podcast/ScriptViewer.vue'
import dayjs from 'dayjs'

const route = useRoute()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const episode = ref(null)
const comments = ref([])
const commentText = ref('')
const commenting = ref(false)
const shareDialogVisible = ref(false)
const shareLoading = ref(false)
const shareError = ref('')
const shareCardData = ref(null)
const sharePosterDataUrl = ref('')
const shareCanvasRef = ref(null)

const isAuthenticated = computed(() => authStore.isAuthenticated)

const isCreator = computed(() => {
  if (!isAuthenticated.value || !episode.value) return false
  return episode.value.show.creator.id === authStore.user.id
})
const isFollowing = computed(() => Boolean(episode.value?.show?.is_following))

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

async function handleFollow() {
  try {
    const data = await api.interactions.toggleFollow(episode.value.show.id)
    episode.value.show.is_following = data.following
    episode.value.show.followers_count = data.followers_count
    ElMessage.success(data.following ? '订阅成功' : '已取消订阅')
  } catch (error) {
    ElMessage.error('订阅操作失败')
  }
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

async function openShareCard() {
  if (!episode.value?.id) return
  shareDialogVisible.value = true
  shareLoading.value = true
  shareError.value = ''
  try {
    shareCardData.value = await api.podcasts.getEpisodeShareCard(episode.value.id)
    await nextTick()
    await renderSharePoster()
  } catch (error) {
    shareError.value = error.response?.data?.error || error.message || '获取分享卡片失败'
  } finally {
    shareLoading.value = false
  }
}

async function renderSharePoster() {
  const canvas = shareCanvasRef.value
  if (!canvas || !shareCardData.value) return
  const ctx = canvas.getContext('2d')
  const data = shareCardData.value

  const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
  gradient.addColorStop(0, '#111827')
  gradient.addColorStop(1, '#1f2937')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.fillStyle = 'rgba(255,255,255,0.08)'
  ctx.fillRect(60, 60, canvas.width - 120, canvas.height - 120)

  if (data.cover_url) {
    try {
      const coverImage = await loadImage(data.cover_url)
      ctx.drawImage(coverImage, 120, 180, 840, 840)
    } catch (error) {
      // ignore cover rendering errors
    }
  }

  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 64px sans-serif'
  drawWrappedText(ctx, data.title || '', 120, 1090, 840, 88)

  ctx.fillStyle = '#9ca3af'
  ctx.font = '44px sans-serif'
  drawWrappedText(ctx, data.show_title || '', 120, 1280, 840, 60)

  ctx.fillStyle = '#d1d5db'
  ctx.font = '36px sans-serif'
  drawWrappedText(ctx, data.description || '', 120, 1360, 840, 52)

  ctx.fillStyle = '#f59e0b'
  ctx.font = 'bold 36px sans-serif'
  drawWrappedText(ctx, data.share_url || '', 120, 1670, 840, 46)

  sharePosterDataUrl.value = canvas.toDataURL('image/png')
}

function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight) {
  if (!text) return
  const chars = String(text).split('')
  let line = ''
  let offsetY = 0
  for (const char of chars) {
    const testLine = line + char
    const testWidth = ctx.measureText(testLine).width
    if (testWidth > maxWidth && line) {
      ctx.fillText(line, x, y + offsetY)
      line = char
      offsetY += lineHeight
    } else {
      line = testLine
    }
  }
  if (line) {
    ctx.fillText(line, x, y + offsetY)
  }
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
}

async function copyShareText() {
  if (!shareCardData.value?.share_text) return
  await navigator.clipboard.writeText(shareCardData.value.share_text)
  ElMessage.success('文案已复制')
}

function downloadSharePoster() {
  if (!sharePosterDataUrl.value) return
  const link = document.createElement('a')
  link.href = sharePosterDataUrl.value
  link.download = `${episode.value?.title || 'share-card'}.png`
  link.click()
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
  flex-wrap: wrap;
}

.episode-actions {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.script-section {
  margin-top: var(--spacing-2xl);
}

.share-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.share-poster {
  width: 100%;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.share-text {
  color: var(--color-text-secondary);
  white-space: pre-line;
}

.share-error {
  color: var(--color-danger);
}

.share-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

.hidden-canvas {
  display: none;
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

@media (max-width: 1024px) {
  .episode-header {
    gap: var(--spacing-lg);
  }

  .episode-cover {
    width: 240px;
    height: 240px;
  }

  .episode-title {
    font-size: var(--font-2xl);
  }
}

@media (max-width: 768px) {
  .episode-detail-page {
    padding: var(--spacing-lg) 0;
  }

  .episode-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .episode-cover {
    width: 100%;
    max-width: 300px;
    height: auto;
    aspect-ratio: 1 / 1;
    margin: 0 auto;
  }

  .episode-title {
    font-size: var(--font-xl);
  }

  .show-name {
    font-size: var(--font-base);
  }

  .episode-meta {
    gap: var(--spacing-sm);
    font-size: var(--font-sm);
  }

  .episode-actions :deep(.el-button) {
    flex: 1 1 auto;
  }

  .share-actions {
    justify-content: stretch;
  }

  .share-actions :deep(.el-button) {
    flex: 1 1 0;
  }

  .comment-user {
    flex-wrap: wrap;
    row-gap: 2px;
  }
}

@media (max-width: 480px) {
  .episode-detail-page {
    padding: var(--spacing-md) 0;
  }

  .episode-header {
    padding: var(--spacing-md);
  }

  .episode-title {
    font-size: var(--font-lg);
  }

  .section-title {
    font-size: var(--font-xl);
  }

  .comment-item {
    padding: var(--spacing-sm);
  }
}
</style>
