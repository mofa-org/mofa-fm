<template>
  <div class="auth-page">
    <div class="auth-card mofa-card">
      <h2 class="auth-title">忘记密码</h2>
      <p class="auth-subtitle">请输入您的注册邮箱，我们将向您发送重置密码的链接。</p>
      
      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label>邮箱地址</label>
          <input 
            v-model="email" 
            type="email" 
            placeholder="your@email.com" 
            required 
            class="form-input"
            :disabled="loading"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>

        <button type="submit" class="mofa-btn mofa-btn-primary full-width" :disabled="loading">
          {{ loading ? '发送中...' : '发送重置链接' }}
        </button>
        
        <div class="auth-links">
          <router-link to="/login">返回登录</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'

const email = ref('')
const loading = ref(false)
const error = ref('')
const successMessage = ref('')

async function handleSubmit() {
  if (!email.value) return
  
  loading.value = true
  error.value = ''
  successMessage.value = ''
  
  try {
    await api.auth.requestPasswordReset(email.value)
    successMessage.value = '重置链接已发送到您的邮箱，请查收（如果是本地测试，请查看后端控制台）。'
    email.value = ''
  } catch (err) {
    if (err.response?.data?.email) {
       error.value = err.response.data.email[0]
    } else {
       error.value = err.response?.data?.error || '请求失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
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

.auth-title {
  text-align: center;
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-2xl);
}

.auth-subtitle {
  text-align: center;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
  font-size: var(--font-sm);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.auth-links {
  text-align: center;
  margin-top: var(--spacing-md);
  font-size: var(--font-sm);
}

.auth-links a {
  color: var(--color-primary);
  text-decoration: none;
}

.auth-links a:hover {
  text-decoration: underline;
}

.success-message {
  color: var(--color-success);
  background: rgba(16, 185, 129, 0.1);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
}

.error-message {
  color: var(--color-error);
  font-size: var(--font-sm);
}
</style>
