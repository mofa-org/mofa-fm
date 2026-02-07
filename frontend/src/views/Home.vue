<template>
  <div class="home-page">
    <div class="container">
      <!-- Hero 区域 -->
      <section class="hero">
        <img src="/logo.png" alt="MoFA FM" class="hero-logo float-animation" />
        <h1 class="hero-title">欢迎来到 MoFA FM</h1>
        <p class="hero-subtitle">人人可创作，人人可收听</p>
        <div class="hero-actions">
          <router-link v-if="!isAuthenticated" to="/register" class="mofa-btn mofa-btn-primary">
            立即开始
          </router-link>
          <router-link to="/discover" class="mofa-btn">
            探索音频
          </router-link>
        </div>
      </section>

      <!-- AI功能区 -->
      <section class="section ai-features" v-if="isAuthenticated">
        <h2 class="section-title">创作入口</h2>
        <div class="feature-cards">
          <router-link to="/creator/ai-studio" class="feature-card mofa-card">
            <div class="feature-icon">
              <el-icon :size="32"><Edit /></el-icon>
            </div>
            <h3 class="feature-title">开始创作</h3>
            <p class="feature-desc">链接、RSS、脚本、辩论模式统一在同一创作页完成</p>
            <div class="feature-action">进入创作 →</div>
          </router-link>
          <router-link to="/creator" class="feature-card mofa-card">
            <div class="feature-icon">
              <el-icon :size="32"><ChatDotRound /></el-icon>
            </div>
            <h3 class="feature-title">内容管理</h3>
            <p class="feature-desc">统一管理我的音频、频道与发布记录</p>
            <div class="feature-action">进入管理 →</div>
          </router-link>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <h2 class="section-title">为你推荐</h2>
          <router-link class="section-more" to="/discover">查看全部</router-link>
        </div>
        <div class="recommended-list" v-if="recommendedItems.length > 0">
          <div
            v-for="item in recommendedItems"
            :key="item.episode.id"
            class="recommended-item"
          >
            <div class="recommended-reason">{{ item.reason }}</div>
            <EpisodeCard
              :episode="item.episode"
              :playlist="recommendedEpisodes"
            />
          </div>
        </div>
        <el-empty v-else description="推荐位加载中" />
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

      <!-- 统计数据（置于页面底部） -->
      <section class="stats" v-if="stats">
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_shows }}</div>
          <div class="stat-label">音频频道</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_episodes }}</div>
          <div class="stat-label">音频单集</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_creators }}</div>
          <div class="stat-label">创作用户</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ formatNumber(stats.total_plays) }}</div>
          <div class="stat-label">总播放量</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ChatDotRound, Edit } from '@element-plus/icons-vue'
import api from '@/api'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'

const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const stats = ref(null)
const recommendedItems = ref([])
const latestEpisodes = ref([])
const recommendedEpisodes = computed(() =>
  recommendedItems.value.map(item => item.episode).filter(Boolean)
)

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

  // 加载推荐位
  try {
    const data = await api.podcasts.getRecommendedEpisodes({ limit: 6 })
    recommendedItems.value = data.items || []
  } catch (error) {
    console.error('加载推荐位失败', error)
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
  margin-top: var(--spacing-xl);
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

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.section-more {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
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

.recommended-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.recommended-item {
  position: relative;
}

.recommended-reason {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  z-index: 2;
  background: rgba(13, 21, 49, 0.75);
  color: #fff;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: var(--font-xs);
}

/* AI功能区 */
.ai-features {
  margin-bottom: var(--spacing-3xl);
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
}

.feature-card {
  padding: var(--spacing-xl);
  text-align: center;
  transition: all 0.3s ease;
  text-decoration: none;
  color: inherit;
  display: block;
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.02),
    rgba(109, 202, 208, 0.02)
  );
  border: 2px solid transparent;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary);
  box-shadow: 0 8px 24px rgba(255, 81, 59, 0.15);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
}

.feature-title {
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
}

.feature-desc {
  font-size: var(--font-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
  line-height: 1.6;
}

.feature-action {
  font-size: var(--font-base);
  color: var(--color-primary);
  font-weight: var(--font-semibold);
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

  .feature-cards {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  .feature-card {
    padding: var(--spacing-lg);
  }

  .feature-icon {
    font-size: 2.5rem;
  }

  .section {
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--font-xl);
  }

  .section-header {
    align-items: flex-end;
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

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
  }

  .shows-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
}
</style>
