<template>
  <router-link :to="`/shows/${show.slug}`" class="show-card mofa-card">
    <div class="show-cover-wrapper">
      <img :src="show.cover_url" :alt="show.title" class="show-cover" />
      <!-- 可见性徽章 -->
      <div v-if="visibilityBadge" class="visibility-badge" :class="`badge-${show.visibility}`">
        <el-icon><component :is="visibilityBadge.icon" /></el-icon>
        <span>{{ visibilityBadge.text }}</span>
      </div>
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
import { computed } from 'vue'
import { Lock, View, User, Share } from '@element-plus/icons-vue'

const props = defineProps({
  show: {
    type: Object,
    required: true
  }
})

const visibilityBadge = computed(() => {
  // 只对非公开的显示徽章
  if (!props.show.visibility || props.show.visibility === 'public') {
    return null
  }

  const badges = {
    private: { text: '私有', icon: Lock, color: '#ff513b' },
    unlisted: { text: '不公开列出', icon: View, color: '#ffc63e' },
    followers: { text: '仅关注者', icon: User, color: '#6dcad0' },
    shared: { text: '已分享', icon: Share, color: '#fd553f' }
  }

  return badges[props.show.visibility] || null
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

/* 可见性徽章 */
.visibility-badge {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  border-radius: 6px;
  font-size: 11px;
  font-weight: var(--font-semibold);
  color: white;
  z-index: 2;
  transition: all 0.2s;
}

.visibility-badge .el-icon {
  font-size: 12px;
}

.badge-private {
  background: rgba(255, 81, 59, 0.9);
}

.badge-unlisted {
  background: rgba(255, 198, 62, 0.9);
}

.badge-followers {
  background: rgba(109, 202, 208, 0.9);
}

.badge-shared {
  background: rgba(253, 85, 63, 0.9);
}

.show-card:hover .visibility-badge {
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
