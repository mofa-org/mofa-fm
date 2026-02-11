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
              <el-avatar :size="40" :src="comment.user.avatar_url || '/default_avatar.png'" />
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
import { VideoPlay, Star, Bell, Share, Download, DocumentCopy, Loading } from '@element-plus/icons-vue'
import QRCode from 'qrcode'
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

  // 纯白背景
  ctx.fillStyle = '#FFFFFF'
  ctx.fillRect(0, 0, w, h)

  // 顶部 Logo - 面积*8 (原50 -> 140)
  try {
    const logoImage = await loadImage('/logo.png')
    const logoSize = 140
    ctx.drawImage(logoImage, 60, 40, logoSize, logoSize)
  } catch (e) {
    ctx.fillStyle = '#FF513B'
    ctx.font = 'bold 80px sans-serif'
    ctx.fillText('MoFA FM', 60, 120)
  }

  // 主封面 - 面积*2 (原320 -> 450)
  const coverSize = 450
  const coverX = (w - coverSize) / 2
  const coverY = 220

  if (data.cover_url) {
    try {
      const coverImage = await loadImage(data.cover_url)
      ctx.drawImage(coverImage, coverX, coverY, coverSize, coverSize)
    } catch (error) {
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(coverX, coverY, coverSize, coverSize)
    }
  }

  // 底部区域固定位置
  const bottomY = h - 280

  // 左侧：mofa.fm 品牌文字 - 字体*2 (原36 -> 72)
  ctx.fillStyle = '#1a1a1a'
  ctx.font = 'bold 72px "PingFang SC", sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('mofa.fm', 60, bottomY + 80)

  // powered by mofa.ai - 字体*2 (原16 -> 32)
  ctx.fillStyle = '#888888'
  ctx.font = '32px "PingFang SC", sans-serif'
  ctx.fillText('powered by mofa.ai', 60, bottomY + 140)

  // 右侧：二维码 - 面积*4 (原100 -> 200)
  const qrSize = 200
  const qrX = w - qrSize - 60
  const qrY = bottomY - 20

  // 绘制二维码
  await drawQRCode(ctx, data.share_url || 'https://mofa.fm', qrX, qrY, qrSize)

  // 扫码提示 - 字体*2 (原14 -> 28)
  ctx.fillStyle = '#1a1a1a'
  ctx.font = 'bold 28px "PingFang SC", sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('扫码收听', qrX + qrSize/2, qrY + qrSize + 50)

  // ===== 中间文字区域动态布局 =====
  ctx.textAlign = 'center'

  // 可用空间：封面底部到二维码顶部
  const textAreaTop = coverY + coverSize + 60
  const textAreaBottom = bottomY - 40
  const textAreaHeight = textAreaBottom - textAreaTop

  // 尝试不同字体大小，找到最合适的
  let titleFontSize = 72
  let showNameFontSize = 56
  let descFontSize = 44
  const lineSpacing = 50 // 三段文字之间的相同间距

  // 计算标题行数（预估）
  ctx.font = `bold ${titleFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
  const titleLines = calculateLines(ctx, data.title || '', w - 80)

  // 如果标题会换行，缩小字体
  if (titleLines > 1 && titleFontSize > 56) {
    titleFontSize = 56
    ctx.font = `bold ${titleFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
  }

  // 计算描述行数
  ctx.font = `${descFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
  const descLines = data.description ? calculateLines(ctx, data.description, w - 100) : 0
  const descMaxLines = Math.min(descLines, 2)

  // 计算总高度
  const titleHeight = titleLines === 1 ? titleFontSize : titleFontSize * 1.2 * titleLines
  const descHeight = descMaxLines * (descFontSize * 1.3)
  const totalContentHeight = titleHeight + showNameFontSize + descHeight
  const totalSpacing = 2 * lineSpacing
  const totalHeight = totalContentHeight + totalSpacing

  // 垂直居中在可用区域内
  const startY = textAreaTop + (textAreaHeight - totalHeight) / 2 + titleFontSize

  // 绘制标题
  ctx.fillStyle = '#1a1a1a'
  ctx.font = `bold ${titleFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
  const titleEndY = drawWrappedTextWithReturn(ctx, data.title || '', w / 2, startY, w - 80, titleFontSize * 1.2, 2)

  // 绘制节目名称（与标题等间距）
  ctx.fillStyle = '#6DCAD0'
  ctx.font = `${showNameFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
  const showNameY = titleEndY + lineSpacing + showNameFontSize * 0.8
  ctx.fillText(data.show_title || '', w / 2, showNameY)

  // 绘制描述（与节目名称等间距）
  if (data.description) {
    ctx.fillStyle = '#666666'
    ctx.font = `${descFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
    const descY = showNameY + lineSpacing + descFontSize * 0.5
    drawWrappedTextWithReturn(ctx, data.description, w / 2, descY, w - 100, descFontSize * 1.3, 2)
  }

  ctx.textAlign = 'left'
  sharePosterDataUrl.value = canvas.toDataURL('image/png')
}

// 计算文本需要几行
function calculateLines(ctx, text, maxWidth) {
  const chars = String(text).split('')
  let line = ''
  let lineCount = 1
  for (const char of chars) {
    const testLine = line + char
    const testWidth = ctx.measureText(testLine).width
    if (testWidth > maxWidth && line) {
      line = char
      lineCount++
    } else {
      line = testLine
    }
  }
  return lineCount
}

// 绘制换行文字并返回最终Y坐标
function drawWrappedTextWithReturn(ctx, text, x, y, maxWidth, lineHeight, maxLines = 0) {
  if (!text) return y
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
        if (chars.indexOf(char) < chars.length - 1) {
          ctx.fillText('...', x + ctx.measureText(line).width, y + offsetY)
        }
        return y + offsetY
      }
    } else {
      line = testLine
    }
  }
  if (line) {
    ctx.fillText(line, x, y + offsetY)
  }
  return y + offsetY
}

// 绘制标准黑白二维码
async function drawQRCode(ctx, text, x, y, size) {
  try {
    const qrData = await QRCode.create(text, { errorCorrectionLevel: 'H' })
    const modules = qrData.modules.size
    const moduleSize = size / modules

    ctx.fillStyle = '#000000'
    for (let row = 0; row < modules; row++) {
      for (let col = 0; col < modules; col++) {
        if (qrData.modules.get(row, col)) {
          ctx.fillRect(x + col * moduleSize, y + row * moduleSize, moduleSize, moduleSize)
        }
      }
    }
  } catch (e) {
    ctx.fillStyle = '#000000'
    ctx.fillRect(x, y, size, size)
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
