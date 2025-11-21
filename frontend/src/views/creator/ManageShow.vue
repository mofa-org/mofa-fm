<template>
  <div class="manage-show-page" v-if="show">
    <div class="container">
      <!-- 节目信息头部 -->
      <div class="show-header mofa-card">
        <img :src="show.cover_url" :alt="show.title" class="show-cover" />
        <div class="show-info">
          <h1 class="show-title">{{ show.title }}</h1>
          <p class="show-meta">{{ show.episodes_count }} 集 · {{ show.followers_count }} 关注</p>
          <div class="show-actions">
            <router-link :to="`/creator/shows/${show.slug}/episodes/create`" class="mofa-btn mofa-btn-primary">
              <el-icon><Plus /></el-icon>
              上传单集
            </router-link>
            <router-link :to="`/shows/${show.slug}`" class="mofa-btn">
              查看公开页面
            </router-link>
            <router-link :to="`/creator/shows/${show.slug}/edit`" class="mofa-btn">
              编辑节目
            </router-link>
          </div>
        </div>
      </div>

      <!-- 单集列表 -->
      <h2 class="section-title">单集管理</h2>
      <div class="episodes-list">
        <div
          v-for="episode in episodes"
          :key="episode.id"
          class="episode-item mofa-card"
          :class="{ highlighted: highlightSlug === episode.slug }"
          :data-episode-slug="episode.slug"
        >
          <img :src="episode.cover_url" :alt="episode.title" class="episode-cover" @click="handlePlay(episode)" />
          <div class="episode-info">
            <h3 class="episode-title">{{ episode.title }}</h3>
            <p class="episode-meta">
              <span>{{ formatDuration(episode.duration) }}</span>
              <span>{{ episode.play_count }} 播放</span>
              <span>{{ formatDate(episode.published_at) }}</span>
            </p>
            <p class="episode-status">状态: {{ getStatusText(episode.status) }}</p>
          </div>
          <div class="episode-actions">
            <router-link
              :to="`/creator/shows/${show.slug}/episodes/${episode.slug}/edit`"
              class="mofa-btn mofa-btn-sm"
            >
              编辑
            </router-link>
            <button @click="handleDelete(episode)" class="mofa-btn mofa-btn-danger mofa-btn-sm">
              删除
            </button>
          </div>
        </div>
      </div>

      <el-empty v-if="episodes.length === 0" description="还没有上传单集">
        <router-link :to="`/creator/shows/${show.slug}/episodes/create`" class="mofa-btn mofa-btn-primary">
          立即上传
        </router-link>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import api from '@/api'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()

const show = ref(null)
const episodes = ref([])
const highlightSlug = ref(null)

onMounted(async () => {
  await loadShow()
  await loadEpisodes()
  await highlightEpisodeIfNeeded()
})

async function loadShow() {
  const slug = route.params.slug
  show.value = await api.podcasts.getShow(slug)
}

async function loadEpisodes() {
  const slug = route.params.slug
  const data = await api.podcasts.getEpisodes({ show_slug: slug })
  episodes.value = data.results || data
}

watch(
  () => route.query.highlightEpisode,
  async () => {
    await highlightEpisodeIfNeeded()
  }
)

async function highlightEpisodeIfNeeded() {
  const slug = route.query.highlightEpisode
  if (!slug) return
  highlightSlug.value = slug
  await nextTick()
  const el = document.querySelector(`[data-episode-slug="${slug}"]`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setTimeout(() => {
      if (highlightSlug.value === slug) {
        highlightSlug.value = null
      }
    }, 3000)
  }
}

function handlePlay(episode) {
  playerStore.play(episode, episodes.value)
}

async function handleDelete(episode) {
  try {
    await ElMessageBox.confirm(
      `确定要删除单集"${episode.title}"吗？删除后无法恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await api.podcasts.deleteEpisode(episode.id)
    ElMessage.success('删除成功')
    await loadEpisodes()
    await loadShow() // 重新加载节目以更新单集数量
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
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}

function getStatusText(status) {
  const statusMap = {
    draft: '草稿',
    processing: '处理中',
    published: '已发布',
    failed: '处理失败'
  }
  return statusMap[status] || status
}
</script>

<style scoped>
.manage-show-page {
  padding: var(--spacing-xl) 0;
}

.show-header {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
  padding: var(--spacing-xl);
}

.show-cover {
  width: 160px;
  height: 160px;
  object-fit: cover;
  border-radius: var(--radius-lg);
}

.show-info {
  flex: 1;
}

.show-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-sm);
}

.show-meta {
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-md);
}

.show-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.section-title {
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.episode-item {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  padding: var(--spacing-md);
}

.episode-item.highlighted {
  border: 2px solid var(--color-primary);
  box-shadow: 0 0 0 4px rgba(255, 81, 59, 0.15);
}

.episode-cover {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-default);
  cursor: pointer;
  transition: var(--transition);
}

.episode-cover:hover {
  opacity: 0.8;
}

.episode-info {
  flex: 1;
  min-width: 0;
}

.episode-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-primary);
}

.episode-meta {
  display: flex;
  gap: var(--spacing-md);
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
  margin-bottom: var(--spacing-xs);
}

.episode-status {
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
}

.episode-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .show-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .show-cover {
    width: 120px;
    height: 120px;
  }

  .show-actions {
    justify-content: center;
  }

  .episode-item {
    flex-wrap: wrap;
  }

  .episode-cover {
    width: 60px;
    height: 60px;
  }

  .episode-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 480px) {
  .manage-show-page {
    padding: var(--spacing-md) 0;
  }

  .show-header {
    padding: var(--spacing-md);
  }

  .show-title {
    font-size: var(--font-xl);
  }

  .episode-item {
    padding: var(--spacing-sm);
    gap: var(--spacing-sm);
  }

  .episode-title {
    font-size: var(--font-base);
  }

  .episode-meta {
    gap: var(--spacing-sm);
    font-size: var(--font-xs);
    flex-wrap: wrap;
  }
}
</style>
