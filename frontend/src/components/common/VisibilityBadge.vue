<template>
  <div v-if="badge" class="visibility-badge-inline" :class="`badge-${visibility}`">
    <el-icon><component :is="badge.icon" /></el-icon>
    <span>{{ badge.text }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Lock, View, User, Share } from '@element-plus/icons-vue'

const props = defineProps({
  visibility: {
    type: String,
    default: 'public'
  }
})

const badge = computed(() => {
  // 公开的不显示
  if (props.visibility === 'public') {
    return null
  }

  const badges = {
    private: { text: '私有', icon: Lock },
    unlisted: { text: '不公开列出', icon: View },
    followers: { text: '仅关注者可见', icon: User },
    shared: { text: '仅受邀用户可见', icon: Share }
  }

  return badges[props.visibility] || null
})
</script>

<style scoped>
.visibility-badge-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-default);
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  border: 2px solid currentColor;
  background: white;
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.08);
}

.visibility-badge-inline .el-icon {
  font-size: 16px;
}

.badge-private {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: rgba(255, 81, 59, 0.05);
}

.badge-unlisted {
  color: var(--color-warning);
  border-color: var(--color-warning);
  background: rgba(255, 198, 62, 0.05);
}

.badge-followers {
  color: var(--color-success);
  border-color: var(--color-success);
  background: rgba(109, 202, 208, 0.05);
}

.badge-shared {
  color: var(--color-accent);
  border-color: var(--color-accent);
  background: rgba(253, 85, 63, 0.05);
}
</style>
