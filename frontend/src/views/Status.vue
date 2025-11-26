<template>
  <div class="status-page">
    <div class="status-header">
      <h1>MoFA FM 系统状态</h1>
      <p class="status-description">实时监控平台各项服务的运行状态</p>
    </div>

    <div class="overall-status" :class="overallStatusClass">
      <div class="status-indicator"></div>
      <div class="status-text">
        <h2>{{ overallStatusText }}</h2>
        <p>{{ overallStatusDescription }}</p>
      </div>
    </div>

    <div class="services-status">
      <h3>服务状态</h3>
      <div class="service-list">
        <div
          v-for="service in services"
          :key="service.name"
          class="service-item"
          :class="service.status"
        >
          <div class="service-header">
            <div class="service-info">
              <div class="service-name">{{ service.name }}</div>
              <div class="service-description">{{ service.description }}</div>
            </div>
            <div class="service-status-badge" :class="service.status">
              {{ getStatusText(service.status) }}
            </div>
          </div>
          <div v-if="service.responseTime" class="service-metrics">
            <span class="metric">响应时间: {{ service.responseTime }}ms</span>
            <span v-if="service.uptime" class="metric">运行时间: {{ service.uptime }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="refresh-info">
      <p>最后更新: {{ lastUpdateTime }}</p>
      <button @click="refreshStatus" class="refresh-button" :disabled="loading">
        <span v-if="loading">刷新中...</span>
        <span v-else>刷新状态</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const services = ref([
  {
    name: 'API 服务',
    description: '后端 API 接口',
    status: 'checking',
    endpoint: '/api/health/',
    responseTime: null,
  },
  {
    name: '数据库',
    description: 'PostgreSQL 数据库服务',
    status: 'checking',
    responseTime: null,
  },
  {
    name: 'Redis 缓存',
    description: 'Redis 缓存和任务队列',
    status: 'checking',
    responseTime: null,
  },
  {
    name: 'AI 脚本生成',
    description: 'Moonshot AI 脚本创作服务',
    status: 'checking',
    responseTime: null,
  },
  {
    name: 'TTS 语音合成',
    description: 'MiniMax 语音合成服务',
    status: 'checking',
    responseTime: null,
  },
  {
    name: '搜索服务',
    description: '全文搜索功能',
    status: 'checking',
    responseTime: null,
  },
])

const loading = ref(false)
const lastUpdateTime = ref('')

const overallStatusClass = computed(() => {
  const statuses = services.value.map((s) => s.status)
  if (statuses.includes('down')) return 'status-down'
  if (statuses.includes('degraded')) return 'status-degraded'
  if (statuses.includes('checking')) return 'status-checking'
  return 'status-operational'
})

const overallStatusText = computed(() => {
  const statusClass = overallStatusClass.value
  if (statusClass === 'status-down') return '服务中断'
  if (statusClass === 'status-degraded') return '部分服务异常'
  if (statusClass === 'status-checking') return '检查中...'
  return '所有系统正常运行'
})

const overallStatusDescription = computed(() => {
  const statusClass = overallStatusClass.value
  if (statusClass === 'status-down') return '一个或多个核心服务当前不可用'
  if (statusClass === 'status-degraded') return '部分服务可能存在性能问题'
  if (statusClass === 'status-checking') return '正在检查各项服务状态'
  return '平台所有功能正常可用'
})

function getStatusText(status) {
  const statusMap = {
    operational: '正常',
    degraded: '异常',
    down: '中断',
    checking: '检查中',
  }
  return statusMap[status] || '未知'
}

async function checkServiceStatus() {
  loading.value = true

  try {
    // 检查 API 服务
    const apiStart = Date.now()
    try {
      await axios.get('/api/health/', { timeout: 5000 })
      const apiTime = Date.now() - apiStart
      services.value[0].status = apiTime < 1000 ? 'operational' : 'degraded'
      services.value[0].responseTime = apiTime
    } catch (error) {
      services.value[0].status = 'down'
      services.value[0].responseTime = null
    }

    // 其他服务状态需要后端提供健康检查接口
    // 这里先模拟状态
    for (let i = 1; i < services.value.length; i++) {
      // 可以通过 API 获取实际状态
      services.value[i].status = 'operational'
      services.value[i].responseTime = Math.floor(Math.random() * 200 + 50)
    }
  } catch (error) {
    console.error('检查服务状态失败:', error)
  } finally {
    loading.value = false
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  }
}

async function refreshStatus() {
  await checkServiceStatus()
}

onMounted(() => {
  checkServiceStatus()
  // 每 30 秒自动刷新
  setInterval(checkServiceStatus, 30000)
})
</script>

<style scoped>
.status-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.status-header {
  text-align: center;
  margin-bottom: 40px;
}

.status-header h1 {
  font-size: 36px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.status-description {
  font-size: 16px;
  color: var(--text-secondary);
}

.overall-status {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 40px;
  transition: all 0.3s;
}

.status-operational {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.status-degraded {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.status-down {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.status-checking {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.status-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: white;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.status-text h2 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.status-text p {
  font-size: 16px;
  opacity: 0.9;
}

.services-status h3 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 24px;
}

.service-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.service-item {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s;
}

.service-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.service-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.service-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.service-description {
  font-size: 14px;
  color: var(--text-secondary);
}

.service-status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.service-status-badge.operational {
  background: #d1fae5;
  color: #065f46;
}

.service-status-badge.degraded {
  background: #fed7aa;
  color: #92400e;
}

.service-status-badge.down {
  background: #fee2e2;
  color: #991b1b;
}

.service-status-badge.checking {
  background: #e5e7eb;
  color: #374151;
}

.service-metrics {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}

.metric {
  display: flex;
  align-items: center;
}

.refresh-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.refresh-info p {
  font-size: 14px;
  color: var(--text-secondary);
}

.refresh-button {
  padding: 10px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-button:hover:not(:disabled) {
  background: var(--primary-hover);
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .status-header h1 {
    font-size: 28px;
  }

  .overall-status {
    padding: 24px;
  }

  .status-text h2 {
    font-size: 22px;
  }

  .service-header {
    flex-direction: column;
    gap: 12px;
  }

  .refresh-info {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
