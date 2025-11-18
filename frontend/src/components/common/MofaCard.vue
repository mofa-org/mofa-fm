<template>
  <div class="mofa-card" :class="{ 'mofa-card-glass': glass }">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  glass: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
/* 已在 main.css 中定义 */
</style>
