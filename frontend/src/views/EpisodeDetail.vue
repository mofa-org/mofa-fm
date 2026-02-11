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
            <button class="mofa-btn mofa-btn-primary mofa-btn-lg" @click="handlePlay">
              <el-icon><VideoPlay /></el-icon>
              播放
            </button>
            <button class="mofa-btn" :disabled="!episode.audio_url" @click="handleDownloadAudio">
              <el-icon><Download /></el-icon>
              {{ episode.audio_url ? '下载音频' : '音频未就绪' }}
            </button>
            <button
              v-if="isAuthenticated"
              class="mofa-btn"
              :class="{ 'mofa-btn-success': isFollowing }"
              @click="handleFollow"
            >
              <el-icon><Bell /></el-icon>
              {{ isFollowing ? '已订阅' : '订阅此节目' }}
            </button>
            <button
              v-if="isAuthenticated"
              class="mofa-btn"
              :class="{ 'is-liked': episode.is_liked }"
              @click="handleLike"
            >
              <el-icon><Star /></el-icon>
              {{ episode.is_liked ? '已点赞' : '点赞' }}
            </button>
            <button class="mofa-btn" @click="openShareCard" :disabled="shareLoading">
              <el-icon><Share /></el-icon>
              分享卡片
            </button>
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
        width="min(480px, 92vw)"
        class="share-dialog"
      >
        <div class="share-panel">
          <div v-if="shareLoading" class="share-loading">
            <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
            <p>正在生成卡片...</p>
          </div>
          <template v-else>
            <div class="share-poster-wrapper">
              <img
                v-if="sharePosterDataUrl"
                :src="sharePosterDataUrl"
                alt="分享海报"
                class="share-poster"
              />
            </div>
            <p v-if="shareError" class="share-error">{{ shareError }}</p>
            <div v-else-if="shareCardData" class="share-text-panel">
              <p class="share-text-label">分享文案</p>
              <div class="share-text-content">{{ shareCardData.share_text }}</div>
            </div>
            <div class="share-actions">
              <button class="mofa-btn" @click="copyShareText" :disabled="!shareCardData">
                <el-icon><DocumentCopy /></el-icon>
                复制文案
              </button>
              <button class="mofa-btn mofa-btn-primary" @click="downloadSharePoster" :disabled="!sharePosterDataUrl">
                <el-icon><Download /></el-icon>
                下载卡片
              </button>
            </div>
          </template>
        </div>
        <canvas ref="shareCanvasRef" width="900" height="1400" class="hidden-canvas"></canvas>
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
import { VideoPlay, Star, UserFilled, Bell, Share, Download, DocumentCopy, Loading } from '@element-plus/icons-vue'
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

function handleDownloadAudio() {
  if (!episode.value?.audio_url) return

  if (window.AndroidBridge?.downloadEpisode) {
    window.AndroidBridge.downloadEpisode(
      episode.value.id,
      episode.value.audio_url,
      episode.value.title,
      episode.value.show?.title || '未知节目'
    )
    return
  }

  const link = document.createElement('a')
  link.href = episode.value.audio_url
  link.download = `${episode.value.title || 'episode'}.mp3`
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
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
  const w = canvas.width
  const h = canvas.height

  // 马卡龙渐变背景 - 柔和的粉色到橙色
  const gradient = ctx.createLinearGradient(0, 0, w, h)
  gradient.addColorStop(0, '#FFF5F5') // 浅粉
  gradient.addColorStop(0.5, '#FFF0E8') // 米白
  gradient.addColorStop(1, '#FFE8E0') // 暖橙
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, w, h)

  // 装饰圆点 - 马卡龙配色
  const dots = [
    { x: 80, y: 100, r: 40, color: 'rgba(255, 179, 186, 0.4)' },
    { x: w - 100, y: 150, r: 60, color: 'rgba(255, 223, 186, 0.4)' },
    { x: 150, y: h - 200, r: 50, color: 'rgba(186, 255, 201, 0.3)' },
    { x: w - 120, y: h - 150, r: 45, color: 'rgba(186, 225, 255, 0.3)' },
  ]
  dots.forEach(dot => {
    ctx.beginPath()
    ctx.arc(dot.x, dot.y, dot.r, 0, Math.PI * 2)
    ctx.fillStyle = dot.color
    ctx.fill()
  })

  // 白色卡片背景
  const cardPadding = 50
  const cardX = cardPadding
  const cardY = cardPadding
  const cardW = w - cardPadding * 2
  const cardH = h - cardPadding * 2

  ctx.fillStyle = 'rgba(255, 255, 255, 0.95)'
  ctx.beginPath()
  ctx.roundRect(cardX, cardY, cardW, cardH, 24)
  ctx.fill()

  // 阴影
  ctx.shadowColor = 'rgba(0, 0, 0, 0.08)'
  ctx.shadowBlur = 20
  ctx.shadowOffsetY = 8
  ctx.fill()
  ctx.shadowColor = 'transparent'

  // 封面区域
  const coverSize = 380
  const coverX = (w - coverSize) / 2
  const coverY = 120

  if (data.cover_url) {
    try {
      const coverImage = await loadImage(data.cover_url)
      // 圆角封面
      ctx.save()
      ctx.beginPath()
      ctx.roundRect(coverX, coverY, coverSize, coverSize, 16)
      ctx.clip()
      ctx.drawImage(coverImage, coverX, coverY, coverSize, coverSize)
      ctx.restore()
    } catch (error) {
      // 封面加载失败时显示占位
      ctx.fillStyle = '#FFE8E0'
      ctx.beginPath()
      ctx.roundRect(coverX, coverY, coverSize, coverSize, 16)
      ctx.fill()
    }
  }

  // 标题
  ctx.fillStyle = '#2D3748'
  ctx.font = 'bold 48px "PingFang SC", "Microsoft YaHei", sans-serif'
  drawWrappedText(ctx, data.title || '', 80, 560, w - 160, 64, 3)

  // 节目名称标签
  const showTagY = 720
  ctx.fillStyle = '#FFF0E8'
  ctx.beginPath()
  ctx.roundRect(80, showTagY - 40, ctx.measureText(data.show_title || '').width + 40, 56, 28)
  ctx.fill()
  ctx.fillStyle = '#FF6B6B'
  ctx.font = '32px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillText(data.show_title || '', 100, showTagY)

  // 描述
  ctx.fillStyle = '#718096'
  ctx.font = '28px "PingFang SC", "Microsoft YaHei", sans-serif'
  drawWrappedText(ctx, data.description || '', 80, 780, w - 160, 44, 3)

  // 分隔线
  ctx.strokeStyle = '#E2E8F0'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(80, 980)
  ctx.lineTo(w - 80, 980)
  ctx.stroke()

  // 二维码区域
  const qrSize = 180
  const qrX = (w - qrSize) / 2
  const qrY = 1020

  // 绘制马卡龙色二维码
  await drawMacaronQRCode(ctx, data.share_url || 'https://mofa.fm', qrX, qrY, qrSize)

  // 扫码提示
  ctx.fillStyle = '#A0AEC0'
  ctx.font = '24px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('扫码收听', w / 2, qrY + qrSize + 40)
  ctx.textAlign = 'left'

  // 品牌标识
  ctx.fillStyle = '#FF6B6B'
  ctx.font = 'bold 32px "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('MoFA FM', w / 2, h - 80)
  ctx.textAlign = 'left'

  sharePosterDataUrl.value = canvas.toDataURL('image/png')
}

// 绘制马卡龙色二维码
async function drawMacaronQRCode(ctx, text, x, y, size) {
  // 简化的二维码效果 - 使用随机方块模拟
  const modules = 25
  const moduleSize = size / modules

  // 背景
  ctx.fillStyle = '#FFFFFF'
  ctx.beginPath()
  ctx.roundRect(x - 10, y - 10, size + 20, size + 20, 12)
  ctx.fill()

  // 马卡龙配色
  const colors = ['#FF9AA2', '#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA']

  for (let row = 0; row < modules; row++) {
    for (let col = 0; col < modules; col++) {
      // 定位点（三个角）
      const isPosition = (row < 7 && col < 7) || (row < 7 && col >= modules - 7) || (row >= modules - 7 && col < 7)

      if (isPosition) {
        ctx.fillStyle = '#2D3748'
      } else {
        // 随机颜色，但保持一定规律
        const colorIndex = (row * col + row + col) % colors.length
        ctx.fillStyle = Math.random() > 0.5 ? colors[colorIndex] : '#FFFFFF'
      }

      if (isPosition || Math.random() > 0.45) {
        const px = x + col * moduleSize
        const py = y + row * moduleSize
        const radius = moduleSize * 0.3
        ctx.beginPath()
        ctx.roundRect(px + 1, py + 1, moduleSize - 2, moduleSize - 2, radius)
        ctx.fill()
      }
    }
  }
}

function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight, maxLines = 0) {
  if (!text) return
  const chars = String(text).split('')
  let line = ''
  let offsetY = 0
  let lineCount = 0
  for (const char of chars) {
    const testLine = line + char
    const testWidth = ctx.measureText(testLine).width
    if (testWidth > maxWidth && line) {
      ctx.fillText(line, x, y + offsetY)
      line = char
      offsetY += lineHeight
      lineCount++
      if (maxLines > 0 && lineCount >= maxLines) {
        // 添加省略号
        if (chars.indexOf(char) < chars.length - 1) {
          ctx.fillText('...', x + ctx.measureText(line).width, y + offsetY - lineHeight)
        }
        break
      }
    } else {
      line = testLine
    }
  }
  if (line && (maxLines === 0 || lineCount < maxLines)) {
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

.episode-actions .mofa-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.episode-actions .mofa-btn-lg {
  padding: 12px 24px;
  font-size: var(--font-lg);
}

.episode-actions .mofa-btn-success {
  background: var(--color-success, #67c23a);
  border-color: var(--color-success, #67c23a);
  color: white;
}

.episode-actions .mofa-btn-success:hover {
  background: var(--color-success-hover, #85ce61);
}

.episode-actions .is-liked {
  color: #ffc63e;
  border-color: #ffc63e;
}

.episode-actions .is-liked:hover {
  background: rgba(255, 198, 62, 0.1);
}

.script-section {
  margin-top: var(--spacing-2xl);
}

.share-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.share-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.share-poster-wrapper {
  display: flex;
  justify-content: center;
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
}

.share-poster {
  max-width: 100%;
  max-height: 400px;
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.share-text-panel {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
}

.share-text-label {
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.share-text-content {
  color: var(--color-text-secondary);
  font-size: var(--font-sm);
  line-height: var(--line-height-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
  padding: var(--spacing-sm);
  background: white;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.share-error {
  color: var(--color-danger);
  text-align: center;
  padding: var(--spacing-md);
}

.share-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
  flex-wrap: wrap;
}

.share-actions .mofa-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 120px;
  justify-content: center;
}

.hidden-canvas {
  display: none;
}

/* 分享对话框样式 */
:deep(.share-dialog .el-dialog__body) {
  padding-top: 0;
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

  .episode-actions .mofa-btn {
    flex: 1 1 auto;
    justify-content: center;
  }

  .share-actions {
    justify-content: stretch;
  }

  .share-actions .mofa-btn {
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
