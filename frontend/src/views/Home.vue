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

      <!-- 最新单集 -->
      <section class="section">
        <h2 class="section-title">最新单集</h2>
        <div class="episodes-list" v-if="latestEpisodes.length > 0">
          <EpisodeCard
            v-for="episode in latestEpisodes"
            :key="episode.id"
            :episode="episode"
            :playlist="latestEpisodes"
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
import api from '@/api'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'

const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const stats = ref(null)
const latestEpisodes = ref([])

onMounted(async () => {
  // 加载统计数据
  try {
    stats.value = await api.podcasts.getStats()
  } catch (error) {
    console.error('加载统计失败', error)
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

/* 响应式优化 */
@media (max-width: 1024px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .shows-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}

@media (max-width: 768px) {
  .home-page {
    padding: var(--spacing-xl) 0;
  }

  .hero {
    padding: var(--spacing-xl) 0;
    margin-bottom: var(--spacing-xl);
  }

  .hero-logo {
    width: 80px;
    height: 80px;
  }

  .hero-title {
    font-size: var(--font-3xl);
  }

  .hero-subtitle {
    font-size: var(--font-lg);
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
    padding: 0 var(--spacing-lg);
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
  }

  .stat-card {
    padding: var(--spacing-md);
  }

  .stat-value {
    font-size: var(--font-2xl);
  }

  .stat-label {
    font-size: var(--font-sm);
  }

  .section {
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--font-xl);
  }

  .shows-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .home-page {
    padding: var(--spacing-lg) 0;
  }

  .hero {
    padding: var(--spacing-lg) 0;
  }

  .hero-logo {
    width: 60px;
    height: 60px;
  }

  .hero-title {
    font-size: var(--font-2xl);
  }

  .hero-subtitle {
    font-size: var(--font-base);
  }

  .hero-actions {
    padding: 0 var(--spacing-md);
  }

  .stats {
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-sm);
  }

  .stat-card {
    padding: var(--spacing-sm);
  }

  .stat-value {
    font-size: var(--font-xl);
  }

  .stat-label {
    font-size: var(--font-xs);
  }

  .section-title {
    font-size: var(--font-lg);
  }

  .shows-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
}
</style>
