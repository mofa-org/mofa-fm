<template>
  <div class="auth-page">
    <div class="auth-container mofa-card">
      <img src="/logo.png" alt="MoFA FM" class="auth-logo" />
      <h2 class="auth-title">登录 MoFA FM</h2>
      <p class="auth-subtitle">探索精彩的播客世界</p>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleSubmit">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名或邮箱"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="mofa-btn mofa-btn-primary"
          style="width: 100%"
          :loading="loading"
          @click="handleSubmit"
        >
          登录
        </el-button>
      </el-form>

      <div class="auth-footer">
        还没有账号？
        <router-link to="/register" class="link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.value)
    ElMessage.success('登录成功')

    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    // 错误已在 API 拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fef5f1 0%, #f0f9ff 100%);
  padding: var(--spacing-lg);
}

.auth-container {
  width: 100%;
  max-width: 400px;
  padding: var(--spacing-2xl);
}

.auth-logo {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--spacing-lg);
  display: block;
  animation: pulse 2s ease-in-out infinite;
}

.auth-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-extrabold);
  text-align: center;
  margin-bottom: var(--spacing-sm);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.auth-subtitle {
  text-align: center;
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-xl);
}

.auth-footer {
  text-align: center;
  margin-top: var(--spacing-lg);
  color: var(--color-text-tertiary);
}

.link {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

.link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .auth-container {
    max-width: 100%;
    padding: var(--spacing-xl);
  }

  .auth-logo {
    width: 64px;
    height: 64px;
  }

  .auth-title {
    font-size: var(--font-2xl);
  }
}

@media (max-width: 480px) {
  .auth-page {
    padding: var(--spacing-sm);
  }

  .auth-container {
    padding: var(--spacing-lg);
  }

  .auth-title {
    font-size: var(--font-xl);
  }

  .auth-subtitle,
  .auth-footer {
    font-size: var(--font-sm);
  }
}
</style>
