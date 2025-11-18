<template>
  <div class="home-page">
    <div class="container">
      <!-- Hero 区域 -->
      <section class="hero">
        <img src="/logo.png" alt="MoFA FM" class="hero-logo float-animation" />
        <h1 class="hero-title">欢迎来到 MoFA FM</h1>
        <p class="hero-subtitle">发现、收听、创作精彩播客</p>
        <div class="hero-actions">
          <router-link v-if="!isAuthenticated" to="/register" class="mofa-btn mofa-btn-primary">
            立即开始
          </router-link>
          <router-link to="/discover" class="mofa-btn">
            探索播客
          </router-link>
        </div>
      </section>

      <!-- 统计数据 -->
      <section class="stats" v-if="stats">
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_shows }}</div>
          <div class="stat-label">播客节目</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_episodes }}</div>
          <div class="stat-label">播客单集</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_creators }}</div>
          <div class="stat-label">创作者</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ formatNumber(stats.total_plays) }}</div>
          <div class="stat-label">总播放量</div>
        </div>
      </section>

      <!-- 精选节目 -->
      <section class="section">
        <h2 class="section-title">精选节目</h2>
        <div class="shows-grid" v-if="featuredShows.length > 0">
          <ShowCard
            v-for="show in featuredShows"
            :key="show.id"
            :show="show"
          />
        </div>
        <el-empty v-else description="暂无精选节目" />
      </section>

      <!-- 最新单集 -->
      <section class="section">
        <h2 class="section-title">最新单集</h2>
        <div class="episodes-list" v-if="latestEpisodes.length > 0">
          <EpisodeCard
            v-for="episode in latestEpisodes"
            :key="episode.id"
            :episode="episode"
          />
        </div>
        <el-empty v-else description="暂无单集" />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usePodcastsStore } from '@/stores/podcasts'
import api from '@/api'
import ShowCard from '@/components/podcast/ShowCard.vue'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'

const authStore = useAuthStore()
const podcastsStore = usePodcastsStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const stats = ref(null)
const latestEpisodes = ref([])

const featuredShows = computed(() => podcastsStore.featuredShows)

onMounted(async () => {
  // 加载统计数据
  try {
    stats.value = await api.podcasts.getStats()
  } catch (error) {
    console.error('加载统计失败', error)
  }

  // 加载精选节目
  try {
    await podcastsStore.fetchFeaturedShows()
  } catch (error) {
    console.error('加载精选节目失败', error)
  }

  // 加载最新单集
  try {
    const data = await api.podcasts.getEpisodes({ page_size: 6 })
    latestEpisodes.value = data.results || data
  } catch (error) {
    console.error('加载最新单集失败', error)
  }
})

function formatNumber(num) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num
}
</script>

<style scoped>
.home-page {
  padding: var(--spacing-2xl) 0;
}

.hero {
  text-align: center;
  padding: var(--spacing-3xl) 0;
  margin-bottom: var(--spacing-2xl);
}

.hero-logo {
  width: 120px;
  height: 120px;
  margin: 0 auto var(--spacing-xl);
  display: block;
}

.hero-title {
  font-size: var(--font-4xl);
  font-weight: var(--font-extrabold);
  margin-bottom: var(--spacing-md);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: var(--font-xl);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

.hero-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-3xl);
}

.stat-card {
  text-align: center;
  padding: var(--spacing-xl);
}

.stat-value {
  font-size: var(--font-4xl);
  font-weight: var(--font-extrabold);
  color: var(--color-primary);
  margin-bottom: var(--spacing-sm);
}

.stat-label {
  font-size: var(--font-base);
  color: var(--color-text-tertiary);
}

.section {
  margin-bottom: var(--spacing-3xl);
}

.section-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-primary);
}

.shows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

@media (max-width: 1024px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: var(--font-3xl);
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
