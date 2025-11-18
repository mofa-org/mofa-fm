<template>
  <img
    src="/logo.png"
    alt="MoFA FM"
    :class="['mofa-logo', sizeClass, { animated: animated }]"
    :style="{ width: customSize, height: customSize }"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'medium', // small, medium, large
    validator: (value) => ['small', 'medium', 'large', 'custom'].includes(value)
  },
  customSize: {
    type: String,
    default: null
  },
  animated: {
    type: Boolean,
    default: false
  }
})

const sizeClass = computed(() => {
  if (props.size === 'custom') return ''
  return `mofa-logo-${props.size}`
})
</script>

<style scoped>
.mofa-logo {
  display: block;
  object-fit: contain;
}

.mofa-logo-small {
  width: 40px;
  height: 40px;
}

.mofa-logo-medium {
  width: 80px;
  height: 80px;
}

.mofa-logo-large {
  width: 120px;
  height: 120px;
}

.mofa-logo.animated {
  animation: pulse 2s ease-in-out infinite;
}

.mofa-logo:hover {
  transform: rotate(-10deg);
  transition: var(--transition);
}
</style>
