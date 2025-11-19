<template>
  <router-link :to="`/shows/${show.slug}`" class="show-card mofa-card">
    <div class="show-cover-wrapper">
      <img :src="show.cover_url" :alt="show.title" class="show-cover" />
    </div>
    <div class="show-info">
      <h3 class="show-title">{{ show.title }}</h3>
      <p class="show-creator">{{ show.creator.username }}</p>
      <div class="show-meta">
        <span>{{ show.episodes_count }} 集</span>
        <span>{{ show.followers_count }} 关注</span>
      </div>
    </div>
  </router-link>
</template>

<script setup>
defineProps({
  show: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.show-card {
  cursor: pointer;
  padding: 0;
  overflow: hidden;
}

.show-cover-wrapper {
  width: 100%;
  padding-top: 100%;
  position: relative;
  overflow: hidden;
  background: var(--color-bg-secondary);
}

.show-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: var(--transition);
}

.show-card:hover .show-cover {
  transform: scale(1.05);
}

.show-info {
  padding: var(--spacing-md);
}

.show-title {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: var(--line-height-tight);
}

.show-creator {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.show-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  flex-wrap: wrap;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .show-info {
    padding: var(--spacing-sm);
  }

  .show-title {
    font-size: var(--font-base);
  }

  .show-creator,
  .show-meta {
    font-size: var(--font-xs);
  }

  .show-meta {
    gap: var(--spacing-sm);
  }
}

@media (max-width: 480px) {
  .show-title {
    font-size: var(--font-sm);
    -webkit-line-clamp: 1;
  }

  .show-meta span {
    font-size: 10px;
  }
}
</style>
