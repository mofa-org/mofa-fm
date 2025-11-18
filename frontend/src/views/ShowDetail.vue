<template>
  <div class="show-detail-page" v-if="show">
    <div class="container">
      <div class="show-header mofa-card">
        <img :src="show.cover_url" :alt="show.title" class="show-cover" />
        <div class="show-info">
          <h1 class="show-title">{{ show.title }}</h1>
          <router-link :to="`/users/${show.creator.username}`" class="creator-name">
            {{ show.creator.username }}
          </router-link>
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
  color: var(--color-primary);
  display: block;
  margin-bottom: var(--spacing-md);
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
</style>
