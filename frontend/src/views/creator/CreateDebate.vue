<template>
  <div class="create-debate">
    <div class="container">
      <h1 class="page-title">创建 AI 辩论 / 会议</h1>

      <div class="mofa-card form-card">
        <form @submit.prevent="handleSubmit">
          <!-- 模式选择 -->
          <div class="form-group">
            <label class="form-label">模式</label>
            <div class="mode-selector">
              <button
                type="button"
                :class="['mode-option', { active: form.mode === 'debate' }]"
                @click="form.mode = 'debate'"
              >
                <div class="mode-icon">
                  <el-icon :size="28"><ChatDotRound /></el-icon>
                </div>
                <div class="mode-name">辩论模式</div>
                <div class="mode-desc">正反双方激烈交锋</div>
              </button>
              <button
                type="button"
                :class="['mode-option', { active: form.mode === 'conference' }]"
                @click="form.mode = 'conference'"
              >
                <div class="mode-icon">
                  <el-icon :size="28"><ChatLineSquare /></el-icon>
                </div>
                <div class="mode-name">会议模式</div>
                <div class="mode-desc">师生共同探讨学习</div>
              </button>
            </div>
          </div>

          <!-- 标题 -->
          <div class="form-group">
            <label class="form-label" for="title">
              {{ form.mode === 'debate' ? '辩论标题' : '会议标题' }} *
            </label>
            <input
              id="title"
              v-model="form.title"
              type="text"
              class="form-input"
              :placeholder="form.mode === 'debate' ? '例如：火星移民辩论' : '例如：深度学习入门'"
              required
            />
            <div class="form-hint">
              {{ form.mode === 'debate'
                ? '标题用于展示，建议简洁明了（如：火星移民辩论、AI取代程序员之争）'
                : '标题用于展示，建议简洁明了（如：深度学习入门、React最佳实践）'
              }}
            </div>
          </div>

          <!-- 主题 -->
          <div class="form-group">
            <label class="form-label" for="topic">
              {{ form.mode === 'debate' ? '辩题' : '学习主题' }} *
            </label>
            <textarea
              id="topic"
              v-model="form.topic"
              class="form-textarea"
              rows="4"
              :placeholder="topicPlaceholder"
              required
            ></textarea>
            <div class="form-hint">
              <strong>{{ form.mode === 'debate' ? '必须明确写出辩题' : '描述想要学习的主题' }}</strong>，{{ form.mode === 'debate'
                ? 'AI将根据此辩题生成辩论内容。例如："人类是否可以火星移民"、"AI是否会取代程序员"'
                : 'AI导师和学生将围绕此展开讨论'
              }}
            </div>
          </div>

          <!-- 轮数 -->
          <div class="form-group">
            <label class="form-label" for="rounds">初始自动轮数</label>
            <div class="rounds-selector">
              <button
                v-for="r in [1, 2, 3]"
                :key="r"
                type="button"
                :class="['round-option', { active: form.rounds === r }]"
                @click="form.rounds = r"
              >
                {{ r }} 轮
              </button>
            </div>
            <div class="form-hint">
              进入辩论页后，可继续输入观点，触发后续群聊
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="form-actions">
            <button
              type="button"
              class="mofa-btn"
              @click="$router.back()"
              :disabled="loading"
            >
              取消
            </button>
            <button
              type="submit"
              class="mofa-btn mofa-btn-primary"
              :disabled="loading"
            >
              {{ loading ? '进入中...' : '进入辩论' }}
            </button>
          </div>

          <!-- 错误提示 -->
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </form>
      </div>

      <!-- 预留：实时流式显示区域 -->
      <!--
      <div v-if="generating" class="mofa-card debate-preview">
        <h3>正在生成...</h3>
        <div class="stream-container">
          // TODO: SSE实时流式显示
        </div>
      </div>
      -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, ChatLineSquare } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const loading = ref(false)
const error = ref('')

const form = ref({
  mode: 'debate',
  title: '',
  topic: '',
  rounds: 1
})

const topicPlaceholder = computed(() => {
  return form.value.mode === 'debate'
    ? '例如：人类是否可以火星移民？正方认为随着科技进步，火星移民是未来发展的必然选择；反方认为火星移民成本过高且技术尚不成熟，应专注于地球可持续发展。'
    : '例如：深度学习的基础原理。包括神经网络、反向传播、梯度下降等核心概念，以及如何应用到实际问题中。'
})

async function handleSubmit() {
  if (!form.value.title || !form.value.topic) {
    error.value = '请填写所有必填项'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await api.podcasts.generateDebate({
      title: form.value.title,
      topic: form.value.topic,
      mode: form.value.mode,
      rounds: form.value.rounds
    })

    const episodeId = data.episode_id

    // 跳转到辩论查看页面
    router.push({
      name: 'debate-viewer',
      params: { episodeId }
    })
  } catch (err) {
    console.error('Failed to create debate:', err)
    error.value = err.response?.data?.error || '创建失败，请稍后重试'
    loading.value = false
  }
}
</script>

<style scoped>
.create-debate {
  padding: 2rem 0;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 2rem;
}

.form-card {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-light-gray);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.form-hint {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

/* 模式选择器 */
.mode-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.mode-option {
  padding: 1.5rem;
  border: 2px solid var(--color-light-gray);
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.mode-option:hover {
  border-color: var(--color-primary-light);
  transform: translateY(-2px);
}

.mode-option.active {
  border-color: var(--color-primary);
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.05),
    rgba(255, 81, 59, 0.1)
  );
}

.mode-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.mode-name {
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}

.mode-desc {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

/* 轮数选择器 */
.rounds-selector {
  display: flex;
  gap: 0.5rem;
}

.round-option {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid var(--color-light-gray);
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.round-option:hover {
  border-color: var(--color-primary-light);
}

.round-option.active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: white;
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
}

/* 响应式 */
@media (max-width: 768px) {
  .mode-selector {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .mofa-btn {
    width: 100%;
  }
}
</style>
