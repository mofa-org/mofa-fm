<template>
  <div class="debate-list">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">我的辩论记录</h1>
        <router-link to="/debate/create" class="mofa-btn mofa-btn-primary">
          <el-icon><Plus /></el-icon>
          创建新辩论
        </router-link>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 辩论列表 -->
      <div v-else-if="debates.length > 0" class="debates-grid">
        <div
          v-for="debate in debates"
          :key="debate.id"
          class="debate-card mofa-card"
          @click="goToDebate(debate.id)"
        >
          <div class="debate-header">
            <div class="debate-mode">
              <el-icon><ChatDotRound v-if="debate.mode === 'debate'" /><ChatLineSquare v-else /></el-icon>
              <span>{{ debate.mode === 'debate' ? '辩论' : '会议' }}</span>
            </div>
            <div class="debate-status" :class="`status-${debate.status}`">
              {{ statusText(debate.status) }}
            </div>
          </div>

          <h3 class="debate-title">{{ debate.title }}</h3>

          <div class="debate-meta">
            <span v-if="debate.dialogue && debate.dialogue.length">
              {{ debate.dialogue.length }} 条对话
            </span>
            <span>{{ formatDate(debate.created_at) }}</span>
          </div>

          <div v-if="debate.status === 'published' && debate.dialogue && debate.dialogue.length > 0" class="debate-preview">
            {{ debate.dialogue[0].content.substring(0, 100) }}...
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-icon :size="64" class="empty-icon"><ChatDotRound /></el-icon>
        <h2>还没有辩论记录</h2>
        <p>创建您的第一场AI辩论，记录精彩观点</p>
        <router-link to="/debate/create" class="mofa-btn mofa-btn-primary">
          创建辩论
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, ChatDotRound, ChatLineSquare } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const debates = ref([])
const loading = ref(true)

onMounted(async () => {
  await loadDebates()
})

async function loadDebates() {
  try {
    loading.value = true
    debates.value = await api.podcasts.getMyDebates()
  } catch (err) {
    console.error('Failed to load debates:', err)
  } finally {
    loading.value = false
  }
}

function goToDebate(debateId) {
  router.push(`/debate/${debateId}`)
}

function statusText(status) {
  const statusMap = {
    processing: '生成中',
    published: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}
</script>

<style scoped>
.debate-list {
  padding: 2rem 0;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 50px;
  height: 50px;
  margin: 0 auto 1rem;
  border: 4px solid var(--color-light-gray);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 辩论网格 */
.debates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.debate-card {
  padding: 1.5rem;
  cursor: pointer;
  transition: var(--transition);
  border: var(--border-width-thin) solid var(--border-color-light);
}

.debate-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary-light);
}

.debate-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.debate-mode {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.08),
    rgba(253, 85, 63, 0.15)
  );
  color: var(--color-primary);
  font-size: 0.875rem;
  font-weight: 500;
}

.debate-status {
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 500;
}

.status-processing {
  background: linear-gradient(135deg,
    rgba(255, 198, 62, 0.15),
    rgba(255, 198, 62, 0.25)
  );
  color: var(--color-warning-dark);
}

.status-published {
  background: linear-gradient(135deg,
    rgba(109, 202, 208, 0.15),
    rgba(109, 202, 208, 0.25)
  );
  color: var(--color-success-dark);
}

.status-failed {
  background: rgba(255, 81, 59, 0.1);
  color: var(--color-primary);
}

.debate-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.75rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.debate-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: 0.75rem;
}

.debate-preview {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color-light);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  color: var(--color-text-tertiary);
  margin-bottom: 1rem;
}

.empty-state h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .debates-grid {
    grid-template-columns: 1fr;
  }
}
</style>
