<template>
  <div class="auth-page">
    <div class="auth-card mofa-card text-center">
      <h2 class="auth-title">邮箱验证</h2>
      
      <div v-if="loading" class="loading-state">
        <p>正在验证您的邮箱，请稍候...</p>
      </div>

      <div v-else-if="success" class="success-state">
        <div class="icon-success">✓</div>
        <p class="message">{{ message }}</p>
        <button @click="goToHome" class="mofa-btn mofa-btn-primary full-width">
          前往首页
        </button>
      </div>

      <div v-else class="error-state">
        <div class="icon-error">!</div>
        <p class="message">{{ message }}</p>
        <button @click="goToHome" class="mofa-btn full-width">
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const success = ref(false)
const message = ref('')

onMounted(async () => {
  const { uid, token } = route.params
  
  if (!uid || !token) {
    loading.value = false
    success.value = false
    message.value = '无效的验证链接'
    return
  }
  
  try {
    const response = await api.auth.verifyEmail({
      uidb64: uid,
      token: token
    })
    
    success.value = true
    message.value = response.message || '邮箱验证成功！'
    
    // 如果用户已登录，更新用户信息
    if (authStore.isAuthenticated) {
      await authStore.fetchUser()
    }
  } catch (err) {
    success.value = false
    message.value = err.response?.data?.error || '验证失败，链接可能已过期'
  } finally {
    loading.value = false
  }
})

function goToHome() {
  router.push('/')
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: var(--spacing-lg);
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: var(--spacing-xl);
}

.text-center {
  text-align: center;
}

.auth-title {
  margin-bottom: var(--spacing-xl);
  font-size: var(--font-2xl);
}

.icon-success {
  font-size: 48px;
  color: var(--color-success);
  margin-bottom: var(--spacing-md);
}

.icon-error {
  font-size: 48px;
  color: var(--color-error);
  margin-bottom: var(--spacing-md);
}

.message {
  margin-bottom: var(--spacing-xl);
  color: var(--color-text-secondary);
}
</style>
