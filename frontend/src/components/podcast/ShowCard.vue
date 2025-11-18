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
}

.show-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.show-info {
  padding: var(--spacing-md);
}

.show-title {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.show-creator {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-sm);
}

.show-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
}
</style>
