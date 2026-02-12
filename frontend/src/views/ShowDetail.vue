<template>
  <div class="show-detail-page" v-if="show">
    <div class="container">
      <div class="show-header mofa-card">
        <img :src="show.cover_url" :alt="show.title" class="show-cover" />
        <div class="show-info">
          <div class="title-row">
            <h1 class="show-title">{{ show.title }}</h1>
            <VisibilityBadge :visibility="show.visibility" />
          </div>
          <div class="creator-name">
            {{ show.creator.username }}
          </div>
          <p class="show-description">{{ show.description }}</p>

          <div class="show-meta">
            <span>{{ show.episodes_count }} 集</span>
            <span>{{ show.followers_count }} 关注</span>
            <span>{{ show.total_plays }} 播放</span>
          </div>

          <div class="show-actions">
            <button
              v-if="isAuthenticated"
              class="mofa-btn"
              :class="{ 'mofa-btn-primary': !isFollowing, 'mofa-btn-success': isFollowing }"
              @click="handleFollow"
            >
              <el-icon><Bell /></el-icon>
              {{ isFollowing ? '已关注' : '关注' }}
            </button>
            <button class="mofa-btn" @click="openShareCard" :disabled="shareLoading">
              <el-icon><Share /></el-icon>
              分享卡片
            </button>
          </div>
        </div>
      </div>

      <!-- 分享卡片对话框 -->
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

      <!-- 单集列表 -->
      <h2 class="section-title">所有单集</h2>
      <div class="episodes-list">
        <EpisodeCard
          v-for="episode in episodes"
          :key="episode.id"
          :episode="episode"
          :show="show"
          :playlist="episodes"
          @deleted="handleEpisodeDeleted"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'
import VisibilityBadge from '@/components/common/VisibilityBadge.vue'
import { ElMessage } from 'element-plus'
import { Bell, Share, Download, DocumentCopy, Loading } from '@element-plus/icons-vue'
import QRCode from 'qrcode'

const route = useRoute()
const authStore = useAuthStore()

const show = ref(null)
const episodes = ref([])
const shareDialogVisible = ref(false)
const shareLoading = ref(false)
const shareError = ref('')
const shareCardData = ref(null)
const sharePosterDataUrl = ref('')
const shareCanvasRef = ref(null)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isFollowing = computed(() => show.value?.is_following)

onMounted(async () => {
  const slug = route.params.slug
  show.value = await api.podcasts.getShow(slug)

  const data = await api.podcasts.getEpisodes({ show_slug: slug })
  episodes.value = data.results || data
})

async function handleFollow() {
  try {
    const data = await api.interactions.toggleFollow(show.value.id)
    show.value.is_following = data.following
    show.value.followers_count = data.followers_count
    ElMessage.success(data.following ? '关注成功' : '取消关注')
  } catch (error) {
    // 错误已处理
  }
}

async function handleEpisodeDeleted(episodeId) {
  // 从列表中移除已删除的单集
  episodes.value = episodes.value.filter(ep => ep.id !== episodeId)
  // 更新单集数量
  if (show.value) {
    show.value.episodes_count--
  }
}

async function openShareCard() {
  if (!show.value?.slug) return
  shareDialogVisible.value = true
  shareLoading.value = true
  shareError.value = ''
  try {
    shareCardData.value = await api.podcasts.getShowShareCard(show.value.slug)
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
  ctx.fillText('扫码订阅', qrX + qrSize/2, qrY + qrSize + 50)

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

  // 绘制创作者名称（与标题等间距）
  ctx.fillStyle = '#6DCAD0'
  ctx.font = `${showNameFontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
  const showNameY = titleEndY + lineSpacing + showNameFontSize * 0.8
  ctx.fillText(data.creator_name || '', w / 2, showNameY)

  // 绘制描述（与创作者名称等间距）
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
  link.download = `${show.value?.title || 'share-card'}.png`
  link.click()
}
</script>

<style scoped>
.show-detail-page {
  padding: var(--spacing-xl) 0;
}

.show-header {
  display: flex;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-2xl);
}

.show-cover {
  width: 300px;
  height: 300px;
  object-fit: cover;
  border-radius: var(--radius-lg);
}

.show-info {
  flex: 1;
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-sm);
}

.show-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin: 0;
}

.creator-name {
  font-size: var(--font-lg);
  color: var(--color-text-secondary);
  display: block;
  margin-bottom: var(--spacing-md);
  font-weight: var(--font-medium);
}

.show-description {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
  line-height: var(--line-height-relaxed);
}

.show-meta {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-tertiary);
}

.show-actions {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.show-actions .mofa-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

.section-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .show-header {
    gap: var(--spacing-lg);
  }

  .show-cover {
    width: 240px;
    height: 240px;
  }

  .show-title {
    font-size: var(--font-2xl);
  }

  .creator-name {
    font-size: var(--font-base);
  }
}

@media (max-width: 768px) {
  .show-detail-page {
    padding: var(--spacing-lg) 0;
  }

  .show-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: var(--spacing-md);
  }

  .show-cover {
    width: 200px;
    height: 200px;
  }

  .show-info {
    width: 100%;
  }

  .show-title {
    font-size: var(--font-xl);
  }

  .show-meta {
    justify-content: center;
    gap: var(--spacing-md);
    font-size: var(--font-sm);
  }

  .section-title {
    font-size: var(--font-xl);
  }
}

@media (max-width: 480px) {
  .show-detail-page {
    padding: var(--spacing-md) 0;
  }

  .show-header {
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
  }

  .show-cover {
    width: 160px;
    height: 160px;
  }

  .show-title {
    font-size: var(--font-lg);
    margin-bottom: var(--spacing-xs);
  }

  .creator-name {
    font-size: var(--font-sm);
    margin-bottom: var(--spacing-sm);
  }

  .show-description {
    font-size: var(--font-sm);
    margin-bottom: var(--spacing-md);
  }

  .show-meta {
    gap: var(--spacing-sm);
    font-size: var(--font-xs);
    flex-wrap: wrap;
  }

  .section-title {
    font-size: var(--font-lg);
    margin-bottom: var(--spacing-md);
    padding: 0 var(--spacing-md);
  }

  .episodes-list {
    gap: var(--spacing-sm);
  }
}
</style>
