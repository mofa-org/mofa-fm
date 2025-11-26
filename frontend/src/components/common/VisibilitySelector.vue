<template>
  <div class="visibility-selector">
    <label class="selector-label">{{ label }}</label>
    <div class="visibility-options">
      <div
        v-for="option in options"
        :key="option.value"
        class="visibility-option"
        :class="{ active: modelValue === option.value }"
        @click="selectOption(option.value)"
      >
        <div class="option-icon" :style="{ background: option.color }">
          <el-icon><component :is="option.icon" /></el-icon>
        </div>
        <div class="option-content">
          <div class="option-title">{{ option.title }}</div>
          <div class="option-description">{{ option.description }}</div>
        </div>
        <el-icon v-if="modelValue === option.value" class="check-icon">
          <Check />
        </el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Connection, Lock, View, User, Share, Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'public'
  },
  label: {
    type: String,
    default: '可见性设置'
  },
  includeInherit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const baseOptions = [
  {
    value: 'public',
    title: '公开',
    description: '所有人都可以看到和搜索到',
    icon: Connection,
    color: 'linear-gradient(135deg, #6dcad0, #8ed9de)'
  },
  {
    value: 'unlisted',
    title: '不公开列出',
    description: '只有知道链接的人可以访问',
    icon: View,
    color: 'linear-gradient(135deg, #ffc63e, #ffd466)'
  },
  {
    value: 'followers',
    title: '仅关注者',
    description: '只有关注了节目的用户可以看到',
    icon: User,
    color: 'linear-gradient(135deg, #6dcad0, #4fb8bf)'
  },
  {
    value: 'shared',
    title: '仅受邀用户',
    description: '只有你分享给的用户可以访问',
    icon: Share,
    color: 'linear-gradient(135deg, #fd553f, #ff7b68)'
  },
  {
    value: 'private',
    title: '私有',
    description: '只有你自己可以看到',
    icon: Lock,
    color: 'linear-gradient(135deg, #ff513b, #fd553f)'
  }
]

const inheritOption = {
  value: 'inherit',
  title: '继承节目设置',
  description: '使用节目的可见性设置',
  icon: Globe,
  color: 'linear-gradient(135deg, #718096, #a0aec0)'
}

const options = computed(() => {
  if (props.includeInherit) {
    return [inheritOption, ...baseOptions]
  }
  return baseOptions
})

function selectOption(value) {
  emit('update:modelValue', value)
}
</script>

<style scoped>
.visibility-selector {
  width: 100%;
}

.selector-label {
  display: block;
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.visibility-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.visibility-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: white;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-default);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.visibility-option:hover {
  border-color: var(--color-primary);
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.08);
}

.visibility-option.active {
  border-color: var(--color-primary);
  background: rgba(255, 81, 59, 0.03);
  box-shadow: 4px 4px 0 rgba(255, 81, 59, 0.1);
}

.option-icon {
  flex: 0 0 48px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-default);
  color: white;
  font-size: 24px;
}

.option-content {
  flex: 1;
}

.option-title {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.option-description {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  line-height: 1.4;
}

.check-icon {
  flex: 0 0 24px;
  font-size: 24px;
  color: var(--color-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .visibility-option {
    padding: var(--spacing-sm);
  }

  .option-icon {
    flex: 0 0 40px;
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .option-title {
    font-size: var(--font-sm);
  }

  .option-description {
    font-size: var(--font-xs);
  }
}
</style>
