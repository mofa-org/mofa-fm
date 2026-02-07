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
            探索播客
          </router-link>
        </div>
      </section>

      <section v-if="isAuthenticated && isCreator" class="section">
        <div class="quick-create mofa-card">
          <div class="quick-header">
            <h2 class="section-title">一键生成音频</h2>
            <router-link to="/creator/ai-studio" class="quick-link">高级模式</router-link>
          </div>
          <p class="quick-tip">贴入 RSS 或网页链接，系统将自动抓取并生成音频任务。</p>
          <div class="quick-grid">
            <el-input
              v-model="quickSourceUrl"
              placeholder="https://news.ycombinator.com/rss 或任意网页链接"
              clearable
            />
            <el-select v-model="quickShowId" placeholder="选择节目">
              <el-option
                v-for="show in myShows"
                :key="show.id"
                :label="show.title"
                :value="show.id"
              />
            </el-select>
            <el-select v-model="quickTemplate" placeholder="选择模板">
              <el-option
                v-for="option in templateOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-input
              v-model="quickTitle"
              placeholder="标题（可选，不填自动生成）"
              clearable
            />
            <button
              class="mofa-btn mofa-btn-success"
              :disabled="quickSubmitting"
              @click="handleQuickGenerate"
            >
              {{ quickSubmitting ? '生成中...' : '一键生成' }}
            </button>
          </div>
          <p v-if="quickError" class="quick-error">{{ quickError }}</p>
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

      <!-- AI功能区 -->
      <section class="section ai-features" v-if="isAuthenticated">
        <h2 class="section-title">AI 创作工具</h2>
        <div class="feature-cards">
          <router-link to="/debates" class="feature-card mofa-card">
            <div class="feature-icon">
              <el-icon :size="32"><FolderOpened /></el-icon>
            </div>
            <h3 class="feature-title">我的辩论</h3>
            <p class="feature-desc">查看所有辩论记录，随时回顾精彩内容</p>
            <div class="feature-action">查看记录 →</div>
          </router-link>
          <router-link to="/debate/create" class="feature-card mofa-card">
            <div class="feature-icon">
              <el-icon :size="32"><ChatDotRound /></el-icon>
            </div>
            <h3 class="feature-title">AI 辩论</h3>
            <p class="feature-desc">让AI参与激烈辩论，生成精彩对话内容</p>
            <div class="feature-action">立即体验 →</div>
          </router-link>
          <router-link to="/creator/ai-studio" class="feature-card mofa-card">
            <div class="feature-icon">
              <el-icon :size="32"><Edit /></el-icon>
            </div>
            <h3 class="feature-title">AI 脚本创作</h3>
            <p class="feature-desc">智能生成 AI 音频脚本，提升创作效率</p>
            <div class="feature-action">开始创作 →</div>
          </router-link>
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
import { ChatDotRound, Edit, FolderOpened } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'

const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isCreator = computed(() => authStore.isCreator)

const stats = ref(null)
const latestEpisodes = ref([])
const myShows = ref([])
const quickSourceUrl = ref('https://news.ycombinator.com/rss')
const quickShowId = ref(null)
const quickTitle = ref('')
const quickSubmitting = ref(false)
const quickError = ref('')
const quickTemplate = ref('news_flash')

const templateOptions = [
  { value: 'web_summary', label: '网页摘要' },
  { value: 'news_flash', label: '新闻快报' },
  { value: 'deep_dive', label: '深度长谈' }
]

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

  if (isAuthenticated.value && isCreator.value) {
    try {
      const data = await api.podcasts.getMyShows()
      myShows.value = Array.isArray(data) ? data : (data.results || [])
      if (!quickShowId.value && myShows.value.length > 0) {
        quickShowId.value = myShows.value[0].id
      }
    } catch (error) {
      console.error('加载节目失败', error)
    }
  }
})

function formatNumber(num) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num
}

async function handleQuickGenerate() {
  if (!quickSourceUrl.value.trim() || !quickShowId.value) {
    quickError.value = '请填写链接并选择节目'
    return
  }

  quickSubmitting.value = true
  quickError.value = ''
  try {
    const response = await api.podcasts.generateEpisodeFromSource({
      show_id: Number(quickShowId.value),
      source_url: quickSourceUrl.value.trim(),
      title: quickTitle.value.trim() || undefined,
      template: quickTemplate.value,
      max_items: 6,
      dry_run: false,
    })
    ElMessage.success(`任务已提交（${response.source_type || 'source'}）`)
    quickTitle.value = ''
  } catch (error) {
    quickError.value = error.response?.data?.error || error.message || '提交失败'
  } finally {
    quickSubmitting.value = false
  }
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

.quick-create {
  padding: var(--spacing-lg);
}

.quick-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.quick-link {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

.quick-tip {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.quick-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-sm);
}

.quick-error {
  color: var(--color-danger);
  margin-top: var(--spacing-sm);
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

  .quick-grid {
    grid-template-columns: 1fr;
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
