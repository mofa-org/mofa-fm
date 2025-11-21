<template>
  <div class="episode-card mofa-card">
    <div class="episode-cover" @click="handlePlay">
      <img :src="episode.cover_url" :alt="episode.title" />
      <div class="play-overlay">
        <el-icon class="play-icon" :size="48">
          <VideoPlay />
        </el-icon>
      </div>
    </div>

    <div class="episode-info">
      <router-link
        :to="`/shows/${episode.show.slug}/episodes/${episode.slug}`"
        class="episode-title"
      >
        {{ episode.title }}
      </router-link>

      <router-link :to="`/shows/${episode.show.slug}`" class="show-name">
        {{ episode.show.title }}
      </router-link>

      <p class="episode-description">{{ episode.description }}</p>

      <div class="episode-meta">
        <span>{{ formatDuration(episode.duration) }}</span>
        <span>{{ episode.play_count }} 播放</span>
        <span>{{ formatDate(episode.published_at) }}</span>
      </div>
    </div>

    <!-- 创作者操作按钮 -->
    <div v-if="showCreatorActions && isCreator" class="episode-actions">
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
import { VideoPlay } from '@element-plus/icons-vue'
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

const resolvedPlaylist = computed(() => {
  if (Array.isArray(props.playlist)) {
    return props.playlist.map(item => (item?.episode ? item.episode : item)).filter(Boolean)
  }
  return null
})

// 判断当前用户是否是该节目的创作者
const isCreator = computed(() => {
  if (!authStore.isAuthenticated || !props.show) return false
  return props.show.creator?.id === authStore.user?.id
})

function handlePlay() {
  playerStore.play(props.episode, resolvedPlaylist.value || null)
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

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: var(--transition);
}

.episode-cover:hover .play-overlay {
  opacity: 1;
}

.play-icon {
  color: white;
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
  color: var(--color-text-tertiary);
  display: block;
  margin-bottom: var(--spacing-sm);
}

.show-name:hover {
  color: var(--color-primary);
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
    opacity: 0.7;
  }

  .play-icon {
    font-size: 32px !important;
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
