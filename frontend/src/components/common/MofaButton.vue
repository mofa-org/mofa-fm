<template>
  <button class="mofa-btn" :class="[type && `mofa-btn-${type}`, size && `mofa-btn-${size}`]">
    <slot />
  </button>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
/* 已在 main.css 中定义 */
</style>
