<template>
  <div class="become-creator-page">
    <div class="container">
      <div class="creator-card mofa-card">
        <img src="/logo.png" alt="MoFA FM" class="card-logo" />
        <h1 class="card-title">开通工作台</h1>
        <p class="card-subtitle">完成简单验证即可开始创作 AI 音频</p>

        <div v-if="!verified" class="verification-section">
          <p style="text-align: center; color: var(--color-text-secondary); margin-bottom: var(--spacing-lg);">
            点击下方按钮即可开通工作台
          </p>

          <el-button
            type="primary"
            size="large"
            class="mofa-btn mofa-btn-primary"
            style="width: 100%"
            :loading="loading"
            @click="handleVerify"
          >
            确定
          </el-button>
        </div>

        <div v-else class="success-section">
          <el-icon class="success-icon" :size="80" color="#6dcad0">
            <SuccessFilled />
          </el-icon>
          <h2 class="success-title">恭喜！您已开通工作台</h2>
          <el-button type="primary" size="large" @click="goToCreatorDashboard">
            前往音频工作台
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { SuccessFilled } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const verified = ref(false)
const loading = ref(false)

onMounted(() => {
  if (authStore.isCreator) {
    verified.value = true
  }
})

async function handleVerify() {
  loading.value = true
  try {
    const data = await api.auth.becomeCreator()

    if (data.success) {
      verified.value = true
      authStore.user.is_creator = true
      ElMessage.success('已开通工作台！')
    } else {
      ElMessage.error(data.message || '操作失败')
    }
  } catch (error) {
    // 如果用户已经是创作者，自动设置为已验证
    if (error.response?.status === 400 && error.response?.data?.error?.includes('已经是创作者')) {
      verified.value = true
    } else {
      ElMessage.error('操作失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

function goToCreatorDashboard() {
  router.push('/creator')
}
</script>

<style scoped>
.become-creator-page {
  min-height: calc(100vh - var(--header-height));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  background: linear-gradient(135deg, #fef5f1 0%, #f0f9ff 100%);
}

.creator-card {
  max-width: 500px;
  width: 100%;
  padding: var(--spacing-2xl);
}

.card-logo {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--spacing-lg);
  display: block;
  animation: pulse 2s ease-in-out infinite;
}

.card-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-extrabold);
  text-align: center;
  margin-bottom: var(--spacing-sm);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.card-subtitle {
  text-align: center;
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-xl);
}

.verification-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.math-question {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.question-label {
  font-size: var(--font-base);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
}

.question-text {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  text-align: center;
  padding: var(--spacing-xl);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-default);
  border: 2px solid var(--border-color-light);
}

.hint-text {
  font-size: var(--font-sm);
  color: var(--color-warning);
  text-align: center;
}

.success-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl) 0;
}

.success-icon {
  animation: pulse 2s ease-in-out infinite;
}

.success-title {
  font-size: var(--font-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
}
</style>
