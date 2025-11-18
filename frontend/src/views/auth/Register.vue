<template>
  <div class="auth-page">
    <div class="auth-container mofa-card">
      <img src="/logo.png" alt="MoFA FM" class="auth-logo" />
      <h2 class="auth-title">注册 MoFA FM</h2>
      <p class="auth-subtitle">开始你的播客之旅</p>

      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="邮箱"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
          />
        </el-form-item>

        <el-form-item prop="password2">
          <el-input
            v-model="form.password2"
            type="password"
            placeholder="确认密码"
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
          注册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号？
        <router-link to="/login" class="link">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = ref({
  username: '',
  email: '',
  password: '',
  password2: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value !== form.value.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  password2: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.register(form.value)
    ElMessage.success('注册成功')
    router.push('/')
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
</style>
