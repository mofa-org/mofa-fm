<template>
  <div class="discover-page">
    <div class="container">
      <h1 class="page-title">发现播客</h1>

      <!-- 分类过滤 -->
      <div class="categories" v-if="categories && categories.length > 0">
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="category-btn mofa-tag"
          :class="{ 'mofa-tag-primary': selectedCategory === cat.id }"
          @click="selectedCategory = cat.id"
        >
          {{ cat.name }}
        </button>
      </div>

      <!-- 播客列表 -->
      <div class="shows-grid" v-loading="loading">
        <ShowCard v-for="show in shows" :key="show.id" :show="show" />
      </div>

      <el-empty v-if="!loading && shows.length === 0" description="暂无播客" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { usePodcastsStore } from "@/stores/podcasts";
import api from "@/api";
import ShowCard from "@/components/podcast/ShowCard.vue";

const podcastsStore = usePodcastsStore();

const selectedCategory = ref(null);
const shows = ref([]);
const loading = ref(false);
const categories = ref([]);

onMounted(async () => {
  categories.value = await podcastsStore.fetchCategories();
  fetchShows();
});

watch(selectedCategory, () => {
  fetchShows();
});

async function fetchShows() {
  loading.value = true;
  try {
    const params = selectedCategory.value
      ? { category: selectedCategory.value }
      : {};
    const data = await api.podcasts.getShows(params);
    shows.value = data.results || data;
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.discover-page {
  padding: var(--spacing-xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
}

.categories {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap;
}

.category-btn {
  cursor: pointer;
  border: none;
  background: var(--color-white);
}

.category-btn.mofa-tag-primary {
  background: var(--gradient-primary);
  color: var(--color-white);
  border: none;
}

.shows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

/* 响应式优化 */
@media (max-width: 1024px) {
  .shows-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}

@media (max-width: 768px) {
  .discover-page {
    padding: var(--spacing-lg) 0;
  }

  .page-title {
    font-size: var(--font-2xl);
    margin-bottom: var(--spacing-md);
  }

  .categories {
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-lg);
  }

  .shows-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .discover-page {
    padding: var(--spacing-md) 0;
  }

  .page-title {
    font-size: var(--font-xl);
  }

  .shows-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
}
</style>
