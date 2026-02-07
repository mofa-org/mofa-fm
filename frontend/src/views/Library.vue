<template>
  <div class="library-page">
    <div class="container">
      <h1 class="page-title">我的收听</h1>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="关注的播客" name="following">
          <div class="shows-grid" v-if="following.length > 0">
            <ShowCard v-for="follow in following" :key="follow.id" :show="follow.show" />
          </div>
          <el-empty v-else description="还没有关注任何播客" />
        </el-tab-pane>

        <el-tab-pane label="播放历史" name="history">
          <div class="episodes-list" v-if="history.length > 0">
            <EpisodeCard
              v-for="item in history"
              :key="item.id"
              :episode="item.episode"
              :playlist="historyEpisodes"
            />
          </div>
          <el-empty v-else description="还没有播放历史" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/api'
import ShowCard from '@/components/podcast/ShowCard.vue'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'

const activeTab = ref('following')
const following = ref([])
const history = ref([])
const historyEpisodes = computed(() => history.value.map(item => item.episode).filter(Boolean))

onMounted(async () => {
  const [followingData, historyData] = await Promise.all([
    api.interactions.getMyFollowing(),
    api.interactions.getMyPlayHistory()
  ])

  following.value = followingData.results || followingData
  history.value = historyData.results || historyData
})
</script>

<style scoped>
.library-page {
  padding: var(--spacing-xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
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

@media (max-width: 768px) {
  .library-page {
    padding: var(--spacing-lg) 0;
  }

  .page-title {
    font-size: var(--font-2xl);
  }

  .shows-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .library-page {
    padding: var(--spacing-md) 0;
  }

  .page-title {
    font-size: var(--font-xl);
    margin-bottom: var(--spacing-md);
  }
}
</style>
