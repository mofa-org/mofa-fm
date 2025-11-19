<template>
  <div class="show-detail-page" v-if="show">
    <div class="container">
      <div class="show-header mofa-card">
        <img :src="show.cover_url" :alt="show.title" class="show-cover" />
        <div class="show-info">
          <h1 class="show-title">{{ show.title }}</h1>
          <div class="creator-name">
            {{ show.creator.username }}
          </div>
          <p class="show-description">{{ show.description }}</p>

          <div class="show-meta">
            <span>{{ show.episodes_count }} 集</span>
            <span>{{ show.followers_count }} 关注</span>
            <span>{{ show.total_plays }} 播放</span>
          </div>

          <el-button
            v-if="isAuthenticated"
            :type="isFollowing ? 'success' : 'primary'"
            @click="handleFollow"
          >
            {{ isFollowing ? '已关注' : '关注' }}
          </el-button>
        </div>
      </div>

      <!-- 单集列表 -->
      <h2 class="section-title">所有单集</h2>
      <div class="episodes-list">
        <EpisodeCard v-for="episode in episodes" :key="episode.id" :episode="episode" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const authStore = useAuthStore()

const show = ref(null)
const episodes = ref([])

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

.show-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-sm);
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
