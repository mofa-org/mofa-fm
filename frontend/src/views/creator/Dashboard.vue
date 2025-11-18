<template>
  <div class="creator-dashboard">
    <div class="container">
      <h1 class="page-title">创作者中心</h1>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.shows_count || 0 }}</div>
          <div class="stat-label">我的节目</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.episodes_count || 0 }}</div>
          <div class="stat-label">发布单集</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_plays || 0 }}</div>
          <div class="stat-label">总播放量</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <router-link to="/creator/shows/create" class="mofa-btn mofa-btn-primary">
          <el-icon><Plus /></el-icon>
          创建新节目
        </router-link>
      </div>

      <!-- 我的节目列表 -->
      <h2 class="section-title">我的节目</h2>
      <div class="shows-list">
        <div v-for="show in shows" :key="show.id" class="show-item mofa-card">
          <img :src="show.cover_url" :alt="show.title" class="show-cover" />
          <div class="show-info">
            <h3 class="show-title">{{ show.title }}</h3>
            <p class="show-meta">{{ show.episodes_count }} 集 · {{ show.followers_count }} 关注</p>
          </div>
          <div class="show-actions">
            <router-link :to="`/creator/shows/${show.id}/episodes/create`">
              <el-button type="primary">上传单集</el-button>
            </router-link>
            <router-link :to="`/shows/${show.slug}`">
              <el-button>查看</el-button>
            </router-link>
          </div>
        </div>
      </div>

      <el-empty v-if="shows.length === 0" description="还没有创建节目" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import { Plus } from '@element-plus/icons-vue'

const authStore = useAuthStore()

const shows = ref([])

const stats = computed(() => authStore.user || {})

onMounted(async () => {
  const data = await api.podcasts.getMyShows()
  shows.value = data.results || data
})
</script>

<style scoped>
.creator-dashboard {
  padding: var(--spacing-xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-xl);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
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

.actions {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
}

.shows-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.show-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
}

.show-cover {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-default);
}

.show-info {
  flex: 1;
}

.show-title {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-xs);
}

.show-meta {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.show-actions {
  display: flex;
  gap: var(--spacing-sm);
}
</style>
