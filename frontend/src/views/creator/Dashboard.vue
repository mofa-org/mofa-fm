<template>
  <div class="creator-dashboard">
    <div class="container">
      <h1 class="page-title">音频工作台</h1>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.shows_count }}</div>
          <div class="stat-label">我的音频</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ shows.reduce((sum, s) => sum + s.episodes_count, 0) }}</div>
          <div class="stat-label">发布单集</div>
        </div>
        <div class="stat-card mofa-card">
          <div class="stat-value">{{ stats.total_plays }}</div>
          <div class="stat-label">总播放量</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <router-link to="/creator/ai-studio" class="mofa-btn mofa-btn-primary">
          <el-icon><ChatDotRound /></el-icon>
          开始创作
        </router-link>
        <router-link to="/creator/shows/create" class="mofa-btn mofa-btn-warning">
          <el-icon><Plus /></el-icon>
          新建节目
        </router-link>
      </div>

      <!-- 我的音频列表 -->
      <h2 class="section-title">我的音频</h2>
      <div class="shows-list">
        <div v-for="show in shows" :key="show.id" class="show-item mofa-card">
          <img :src="show.cover_url" :alt="show.title" class="show-cover" />
          <div class="show-info">
            <h3 class="show-title">{{ show.title }}</h3>
            <p class="show-meta">{{ show.episodes_count }} 集 · {{ show.followers_count }} 关注</p>
          </div>
          <div class="show-actions">
            <router-link :to="`/creator/shows/${show.slug}`" class="mofa-btn mofa-btn-primary mofa-btn-sm">
              管理单集
            </router-link>
            <router-link :to="`/creator/shows/${show.slug}/episodes/create`" class="mofa-btn mofa-btn-sm">
              上传单集
            </router-link>
            <router-link :to="`/creator/shows/${show.slug}/edit`" class="mofa-btn mofa-btn-sm">
              编辑节目
            </router-link>
            <button @click="handleDeleteShow(show)" class="mofa-btn mofa-btn-danger mofa-btn-sm">
              删除
            </button>
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
import { Plus, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()

const shows = ref([])
const stats = ref({
  shows_count: 0,
  total_plays: 0
})

onMounted(async () => {
  await loadShows()
})

async function loadShows() {
  const data = await api.podcasts.getMyShows()
  shows.value = data.results || data

  // 计算统计数据
  stats.value.shows_count = shows.value.length
  stats.value.total_plays = shows.value.reduce((sum, show) => sum + (show.total_plays || 0), 0)
}

async function handleDeleteShow(show) {
  try {
    await ElMessageBox.confirm(
      `确定要删除节目"${show.title}"吗？删除后无法恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await api.podcasts.deleteShow(show.slug)
    ElMessage.success('删除成功')
    await loadShows()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败：', error)
      ElMessage.error('删除失败')
    }
  }
}
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
  display: flex;
  gap: var(--spacing-md);
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
  align-items: center;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .show-item {
    align-items: flex-start;
  }

  .show-actions {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .creator-dashboard {
    padding: var(--spacing-lg) 0;
  }

  .page-title {
    font-size: var(--font-2xl);
    margin-bottom: var(--spacing-lg);
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .show-item {
    flex-direction: column;
  }

  .show-cover {
    width: 100%;
    max-width: 220px;
    height: auto;
    aspect-ratio: 1 / 1;
  }

  .show-info {
    width: 100%;
  }

  .show-actions {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .creator-dashboard {
    padding: var(--spacing-md) 0;
  }

  .page-title {
    font-size: var(--font-xl);
  }
}
</style>
