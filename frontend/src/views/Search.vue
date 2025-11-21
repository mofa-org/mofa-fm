<template>
  <div class="search-page">
    <div class="container">
      <h1 class="page-title">搜索结果</h1>
      <p class="search-query">关键词：{{ query }}</p>

      <div v-if="!loading">
        <!-- 播客节目 -->
        <section v-if="results.shows?.length > 0" class="section">
          <h2 class="section-title">播客节目 ({{ results.shows.length }})</h2>
          <div class="shows-grid">
            <ShowCard v-for="show in results.shows" :key="show.id" :show="show" />
          </div>
        </section>

        <!-- 单集 -->
        <section v-if="results.episodes?.length > 0" class="section">
          <h2 class="section-title">单集 ({{ results.episodes.length }})</h2>
          <div class="episodes-list">
            <EpisodeCard
              v-for="episode in results.episodes"
              :key="episode.id"
              :episode="episode"
              :playlist="results.episodes"
            />
          </div>
        </section>

        <!-- 评论 -->
        <section v-if="results.comments?.length > 0" class="section">
          <h2 class="section-title">评论 ({{ results.comments.length }})</h2>
          <div class="comments-list">
            <div v-for="comment in results.comments" :key="comment.id" class="comment-item mofa-card">
              <p class="comment-text">{{ comment.text }}</p>
              <router-link
                :to="`/shows/${comment.episode.show.slug}/episodes/${comment.episode.slug}`"
                class="comment-link"
              >
                来自: {{ comment.episode.title }}
              </router-link>
            </div>
          </div>
        </section>

        <el-empty v-if="results.total === 0" description="没有找到相关结果" />
      </div>

      <div v-else class="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import ShowCard from '@/components/podcast/ShowCard.vue'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()

const query = ref('')
const results = ref({})
const loading = ref(false)

onMounted(async () => {
  query.value = route.query.q
  if (query.value) {
    await performSearch()
  }
})

async function performSearch() {
  loading.value = true
  try {
    results.value = await api.search.search(query.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-page {
  padding: var(--spacing-xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-sm);
}

.search-query {
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-xl);
}

.section {
  margin-bottom: var(--spacing-2xl);
}

.section-title {
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
  margin-bottom: var(--spacing-lg);
}

.shows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.episodes-list,
.comments-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.comment-item {
  padding: var(--spacing-md);
}

.comment-text {
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-secondary);
}

.comment-link {
  color: var(--color-primary);
  font-size: var(--font-sm);
}

.loading {
  text-align: center;
  padding: var(--spacing-3xl);
  font-size: 48px;
  color: var(--color-primary);
}
</style>
