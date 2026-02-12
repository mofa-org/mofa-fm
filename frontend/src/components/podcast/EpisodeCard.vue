<template>
  <div class="episode-card mofa-card">
    <div class="episode-cover" @click="handlePlay">
      <img
        :src="episode.cover_url"
        :alt="episode.title"
        :class="{ 'placeholder-cover': isPlaceholderCover }"
      />
      <div class="play-overlay">
        <div class="play-button">
          <el-icon class="play-icon" :size="36">
            <VideoPlay />
          </el-icon>
          <span class="play-text">播放</span>
        </div>
      </div>
      <!-- 可见性徽章 -->
      <div v-if="visibilityBadge" class="visibility-badge" :class="`badge-${effectiveVisibility}`">
        <el-icon><component :is="visibilityBadge.icon" /></el-icon>
        <span>{{ visibilityBadge.text }}</span>
      </div>
    </div>

    <div class="episode-info">
      <router-link
        v-if="episode.show"
        :to="`/shows/${episode.show.slug}/episodes/${episode.slug}`"
        class="episode-title"
      >
        {{ episode.title }}
      </router-link>
      <div v-else class="episode-title">
        {{ episode.title }}
      </div>

      <router-link v-if="episode.show" :to="`/shows/${episode.show.slug}`" class="show-name">
        <el-icon><Folder /></el-icon>
        <span>{{ episode.show.title }}</span>
        <el-icon class="arrow-icon"><ArrowRight /></el-icon>
      </router-link>
      <div v-else class="show-name debate-badge">
        {{ episode.mode === 'debate' ? 'AI辩论' : 'AI会议' }}
      </div>

      <p class="episode-description">{{ episode.description }}</p>

      <div class="episode-meta">
        <span>{{ formatDuration(episode.duration) }}</span>
        <span>{{ episode.play_count }} 播放</span>
        <span>{{ formatDate(episode.published_at) }}</span>
      </div>

      <div class="episode-tools">
        <button
          class="mofa-btn mofa-btn-sm"
          :disabled="!episode.audio_url"
          @click.stop="handleDownload"
        >
          <el-icon><Download /></el-icon>
          {{ episode.audio_url ? '下载' : '音频未就绪' }}
        </button>
      </div>
    </div>

    <!-- 创作者操作按钮 -->
    <div v-if="showCreatorActions && isCreator && episode.show" class="episode-actions">
      <router-link
        :to="`/creator/shows/${episode.show.slug}/episodes/${episode.slug}/edit`"
        class="mofa-btn mofa-btn-sm"
      >
        编辑
      </router-link>
      <button @click="handleDelete" class="mofa-btn mofa-btn-danger mofa-btn-sm">
        删除
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { VideoPlay, Lock, View, User, Share, Download, Folder, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import dayjs from 'dayjs'

const props = defineProps({
  episode: {
    type: Object,
    required: true
  },
  show: {
    type: Object,
    default: null
  },
  playlist: {
    type: Array,
    default: null
  },
  showCreatorActions: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['deleted'])

const playerStore = usePlayerStore()
const authStore = useAuthStore()

// 计算实际生效的可见性
const effectiveVisibility = computed(() => {
  if (!props.episode.visibility || props.episode.visibility === 'inherit') {
    return props.episode.show?.visibility || 'public'
  }
  return props.episode.visibility
})

const visibilityBadge = computed(() => {
  const visibility = effectiveVisibility.value

  // 只对非公开的显示徽章
  if (visibility === 'public') {
    return null
  }

  const badges = {
    private: { text: '私有', icon: Lock },
    unlisted: { text: '不公开', icon: View },
    followers: { text: '仅关注者', icon: User },
    shared: { text: '已分享', icon: Share }
  }

  return badges[visibility] || null
})

const resolvedPlaylist = computed(() => {
  if (Array.isArray(props.playlist)) {
    return props.playlist.map(item => (item?.episode ? item.episode : item)).filter(Boolean)
  }
  return null
})

const isPlaceholderCover = computed(() => {
  const url = String(props.episode?.cover_url || '').toLowerCase()
  if (!url) return true
  return (
    url.includes('default_show_logo') ||
    url.includes('default_avatar') ||
    url.includes('default-cover') ||
    url.includes('default_cover') ||
    url.includes('placeholder')
  )
})

// 判断当前用户是否是该节目的创作者
const isCreator = computed(() => {
  if (!authStore.isAuthenticated || !props.show) return false
  return props.show.creator?.id === authStore.user?.id
})

function handlePlay() {
  playerStore.play(props.episode, resolvedPlaylist.value || null)
}

function handleDownload() {
  if (!props.episode?.audio_url) return

  if (window.AndroidBridge?.downloadEpisode) {
    window.AndroidBridge.downloadEpisode(
      props.episode.id,
      props.episode.audio_url,
      props.episode.title,
      props.episode.show?.title || '未知节目'
    )
    return
  }

  const link = document.createElement('a')
  link.href = props.episode.audio_url
  link.download = `${props.episode.title || 'episode'}.mp3`
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除单集"${props.episode.title}"吗？删除后无法恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await api.podcasts.deleteEpisode(props.episode.id)
    ElMessage.success('删除成功')
    emit('deleted', props.episode.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败：', error)
      ElMessage.error('删除失败')
    }
  }
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:00`
  return `${m}:00`
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}
</script>

<style scoped>
.episode-card {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}

.episode-cover {
  flex: 0 0 120px;
  height: 120px;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  border-radius: var(--radius-default);
}

.episode-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.episode-cover img.placeholder-cover {
  object-fit: contain;
  padding: 6px;
  background: #f3f4f6;
}

/* 可见性徽章 */
.episode-cover .visibility-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 6px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(6px);
  border-radius: 4px;
  font-size: 10px;
  font-weight: var(--font-semibold);
  color: white;
  z-index: 2;
}

.episode-cover .visibility-badge .el-icon {
  font-size: 11px;
}

.badge-private {
  background: rgba(255, 81, 59, 0.95) !important;
}

.badge-unlisted {
  background: rgba(255, 198, 62, 0.95) !important;
}

.badge-followers {
  background: rgba(109, 202, 208, 0.95) !important;
}

.badge-shared {
  background: rgba(253, 85, 63, 0.95) !important;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
}

.episode-cover:hover .play-overlay {
  opacity: 1;
  background: rgba(0, 0, 0, 0.4);
}

.play-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 50%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transform: scale(0.8);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.episode-cover:hover .play-button {
  transform: scale(1);
}

.play-button:hover {
  background: white;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.play-icon {
  color: var(--color-primary);
}

.play-text {
  font-size: 11px;
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
}

.episode-info {
  flex: 1;
  min-width: 0;
}

.episode-title {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  display: block;
  margin-bottom: var(--spacing-xs);
}

.episode-title:hover {
  color: var(--color-primary);
}

.show-name {
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-bottom: var(--spacing-sm);
  padding: 2px 8px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.show-name:hover {
  background: var(--color-primary);
  color: white;
}

.show-name .arrow-icon {
  font-size: 12px;
  opacity: 0;
  transform: translateX(-4px);
  transition: var(--transition);
}

.show-name:hover .arrow-icon {
  opacity: 1;
  transform: translateX(0);
}

.episode-description {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episode-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
}

.episode-tools {
  margin-top: var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.episode-actions {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .episode-cover {
    flex: 0 0 100px;
    height: 100px;
  }

  /* 移动端始终显示播放按钮 */
  .play-overlay {
    opacity: 1;
    background: rgba(0, 0, 0, 0.25);
  }

  .play-button {
    transform: scale(0.85);
    padding: 10px 16px;
  }

  .play-text {
    display: none;
  }

  .episode-title {
    font-size: var(--font-base);
  }

  .episode-meta {
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .episode-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .episode-card {
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .episode-cover {
    flex: 0 0 80px;
    height: 80px;
  }

  .play-overlay {
    opacity: 1;
    background: rgba(0, 0, 0, 0.2);
  }

  .play-button {
    transform: scale(0.75);
    padding: 8px 12px;
  }

  .play-text {
    display: none;
  }

  .episode-title {
    font-size: var(--font-sm);
    margin-bottom: 4px;
  }

  .show-name {
    font-size: var(--font-xs);
    margin-bottom: var(--spacing-xs);
  }

  .episode-description {
    font-size: var(--font-xs);
    margin-bottom: var(--spacing-xs);
    -webkit-line-clamp: 1;
  }

  .episode-meta {
    gap: var(--spacing-xs);
    font-size: 10px;
  }

  .episode-meta span {
    white-space: nowrap;
  }

  .episode-actions {
    width: 100%;
    flex-direction: row;
    justify-content: flex-end;
  }
}
</style>
