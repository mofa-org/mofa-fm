<template>
  <div class="auth-page">
    <div class="auth-card mofa-card">
      <h2 class="auth-title">重置密码</h2>
      
      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label>新密码</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="请输入新密码" 
            required 
            class="form-input"
            minlength="8"
          />
        </div>
        
        <div class="form-group">
          <label>确认新密码</label>
          <input 
            v-model="confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码" 
            required 
            class="form-input"
            minlength="8"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="mofa-btn mofa-btn-primary full-width" :disabled="loading">
          {{ loading ? '提交中...' : '重置密码' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  loading.value = true
  error.value = ''
  
  const { uid, token } = route.params
  
  try {
    await api.auth.confirmPasswordReset({
      uidb64: uid,
      token: token,
      new_password: password.value,
      re_new_password: confirmPassword.value
    })
    
    ElMessage.success('密码重置成功，请使用新密码登录')
    router.push('/login')
  } catch (err) {
    if (err.response?.data?.new_password) {
       error.value = err.response.data.new_password[0]
    } else if (err.response?.data?.error) {
       error.value = err.response.data.error
    } else {
       error.value = '重置失败，链接可能已失效'
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
  margin-bottom: var(--spacing-xl);
  font-size: var(--font-2xl);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.error-message {
  color: var(--color-error);
  font-size: var(--font-sm);
}
</style>
