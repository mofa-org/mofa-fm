<template>
  <div class="become-creator-page">
    <div class="container">
      <div class="creator-card mofa-card">
        <img src="/logo.png" alt="MoFA FM" class="card-logo" />
        <h1 class="card-title">成为创作者</h1>
        <p class="card-subtitle">完成简单验证即可开始创作播客</p>

        <div v-if="!verified" class="verification-section">
          <div class="math-question">
            <label class="question-label">请回答以下问题：</label>
            <div class="question-text">{{ question }}</div>
            <el-input
              v-model="answer"
              type="number"
              size="large"
              placeholder="输入答案"
              @keyup.enter="handleVerify"
            />
            <p v-if="attemptsLeft < 3" class="hint-text">
              剩余尝试次数：{{ attemptsLeft }}
            </p>
          </div>

          <el-button
            type="primary"
            size="large"
            class="mofa-btn mofa-btn-primary"
            style="width: 100%"
            :loading="loading"
            @click="handleVerify"
          >
            提交答案
          </el-button>
        </div>

        <div v-else class="success-section">
          <el-icon class="success-icon" :size="80" color="#6dcad0">
            <SuccessFilled />
          </el-icon>
          <h2 class="success-title">恭喜！您已成为创作者</h2>
          <el-button type="primary" size="large" @click="goToCreatorDashboard">
            前往创作中心
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

const question = ref('')
const answer = ref('')
const attemptsLeft = ref(3)
const verified = ref(false)
const loading = ref(false)

onMounted(async () => {
  if (authStore.isCreator) {
    verified.value = true
    return
  }

  try {
    const data = await api.auth.becomeCreator()
    question.value = data.question
    attemptsLeft.value = 3 - data.attempts
  } catch (error) {
    console.error('获取验证题目失败', error)
  }
})

async function handleVerify() {
  if (!answer.value) {
    ElMessage.warning('请输入答案')
    return
  }

  loading.value = true
  try {
    const data = await api.auth.verifyCreator({ answer: parseInt(answer.value) })

    if (data.success) {
      verified.value = true
      authStore.user.is_creator = true
      ElMessage.success('验证成功！')
    } else {
      ElMessage.error(data.message)
      attemptsLeft.value = data.attempts_left
      answer.value = ''
    }
  } catch (error) {
    // 错误已处理
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
