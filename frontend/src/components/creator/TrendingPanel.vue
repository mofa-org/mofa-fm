<template>
  <div class="trending-panel mofa-card">
    <div class="panel-header">
      <div class="header-left">
        <span class="header-icon">💡</span>
        <h3>从热门话题获取灵感</h3>
      </div>
      <button @click="collapsed = !collapsed" class="toggle-btn">
        {{ collapsed ? '展开' : '收起' }}
      </button>
    </div>

    <div v-if="!collapsed" class="panel-content">
      <div v-if="loading" class="loading-state">加载热榜中...</div>

      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button @click="loadAllRoutes" class="mofa-btn mofa-btn-sm">重试</button>
      </div>

      <div v-else class="sources-list">
        <div
          v-for="source in sources"
          :key="source.name"
          class="source-item"
        >
          <div class="source-header" @click="toggleSource(source.name)">
            <div class="source-info">
              <span class="expand-icon">{{ expandedSources.includes(source.name) ? '∨' : '>' }}</span>
              <span class="source-title">{{ source.title || source.name }}</span>
              <span class="source-meta">
                <span class="item-count">{{ source.total || 0 }}条</span>
                <span class="update-time">{{ formatUpdateTime(source.updateTime) }}</span>
              </span>
            </div>
            <button
              v-if="!expandedSources.includes(source.name)"
              @click.stop="loadSourceData(source.name)"
              class="load-btn"
              :disabled="loadingSource === source.name"
            >
              {{ loadingSource === source.name ? '加载中...' : '加载' }}
            </button>
          </div>

          <div v-if="expandedSources.includes(source.name)" class="source-content">
            <div v-if="loadingSource === source.name" class="loading-small">
              <span class="loading-text">加载中...</span>
            </div>

            <div v-else-if="source.data && source.data.length > 0" class="trending-list">
              <div
                v-for="(item, index) in source.data.slice(0, showAllItems[source.name] ? source.data.length : 10)"
                :key="item.id || index"
                class="trending-item"
                @click="selectTrendingItem(item, source)"
              >
                <div class="item-rank">{{ index + 1 }}</div>
                <div class="item-content">
                  <div class="item-title">{{ item.title }}</div>
                  <div class="item-meta">
                    <span v-if="item.hot" class="item-hot">🔥 {{ formatHot(item.hot) }}</span>
                    <span v-if="item.author" class="item-author">{{ item.author }}</span>
                  </div>
                </div>
              </div>

              <button
                v-if="source.data.length > 10"
                @click.stop="showAllItems[source.name] = !showAllItems[source.name]"
                class="show-more-btn"
              >
                {{ showAllItems[source.name] ? '收起' : `查看全部 ${source.data.length} 条` }}
              </button>
            </div>

            <div v-else class="empty-state-small">
              暂无数据
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'

const API_BASE = 'http://mofa.fm:1145'

// 状态
const collapsed = ref(false)
const loading = ref(true)
const error = ref('')
const sources = ref([])
const expandedSources = ref([])
const loadingSource = ref(null)
const showAllItems = reactive({})

// Emit 事件
const emit = defineEmits(['select-trending'])

// 加载所有可用的热榜路由
async function loadAllRoutes() {
  loading.value = true
  error.value = ''

  try {
    const response = await axios.get(`${API_BASE}/all`)
    const routesData = response.data.routes || []

    sources.value = routesData.map(route => ({
      name: route.name,
      path: route.path,
      title: route.name.toUpperCase(),
      total: 0,
      updateTime: null,
      data: null
    }))
  } catch (err) {
    console.error('加载热榜列表失败:', err)
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 切换源的展开/收起
function toggleSource(sourceName) {
  const index = expandedSources.value.indexOf(sourceName)
  if (index > -1) {
    expandedSources.value.splice(index, 1)
  } else {
    expandedSources.value.push(sourceName)
    // 如果还没有加载数据，则加载
    const source = sources.value.find(s => s.name === sourceName)
    if (source && !source.data) {
      loadSourceData(sourceName)
    }
  }
}

// 加载特定源的数据
async function loadSourceData(sourceName) {
  const source = sources.value.find(s => s.name === sourceName)
  if (!source) return

  loadingSource.value = sourceName

  try {
    const response = await axios.get(`${API_BASE}${source.path}`)
    const data = response.data

    source.title = data.title || data.name || sourceName
    source.total = data.total || data.data?.length || 0
    source.updateTime = data.updateTime
    source.data = data.data || []

    // 自动展开
    if (!expandedSources.value.includes(sourceName)) {
      expandedSources.value.push(sourceName)
    }
  } catch (err) {
    console.error(`加载 ${sourceName} 失败:`, err)
    source.data = []
  } finally {
    loadingSource.value = null
  }
}

// 选中热搜条目
function selectTrendingItem(item, source) {
  emit('select-trending', {
    item,
    source: source.title || source.name
  })
}

// 格式化热度
function formatHot(hot) {
  if (!hot) return ''
  if (hot >= 100000000) {
    return (hot / 100000000).toFixed(1) + '亿'
  }
  if (hot >= 10000) {
    return (hot / 10000).toFixed(0) + '万'
  }
  return hot.toLocaleString()
}

// 格式化更新时间
function formatUpdateTime(timeString) {
  if (!timeString) return ''

  const now = new Date()
  const updateTime = new Date(timeString)
  const diffMs = now - updateTime
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return '刚刚更新'
  if (diffMins < 60) return `${diffMins}分钟前`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}天前`
}

onMounted(() => {
  loadAllRoutes()
})
</script>

<style scoped>
.trending-panel {
  margin-bottom: var(--spacing-lg);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--border-color);
  margin-bottom: var(--spacing-md);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.header-icon {
  font-size: 20px;
}

.panel-header h3 {
  margin: 0;
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
}

.toggle-btn {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 4px 12px;
  font-size: var(--font-xs);
  cursor: pointer;
  transition: var(--transition);
}

.toggle-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.panel-content {
  max-height: 600px;
  overflow-y: auto;
}

.loading-state,
.error-state {
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-text-tertiary);
}

.error-state p {
  margin-bottom: var(--spacing-sm);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.source-item {
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: var(--transition);
}

.source-item:hover {
  border-color: var(--border-color);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg);
  cursor: pointer;
  user-select: none;
}

.source-header:hover {
  background: var(--color-bg-secondary);
}

.source-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 1;
}

.expand-icon {
  font-family: monospace;
  font-weight: bold;
  color: var(--color-text-tertiary);
  min-width: 16px;
}

.source-title {
  font-weight: var(--font-semibold);
  font-size: var(--font-sm);
}

.source-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.item-count {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

.update-time {
  color: var(--color-text-placeholder);
}

.load-btn {
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 4px 12px;
  font-size: var(--font-xs);
  cursor: pointer;
  transition: var(--transition);
  margin-left: var(--spacing-sm);
}

.load-btn:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.load-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.source-content {
  border-top: 1px solid var(--border-color-light);
  background: white;
}

.loading-small {
  padding: var(--spacing-md);
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
}

.trending-list {
  display: flex;
  flex-direction: column;
}

.trending-item {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: var(--transition);
}

.trending-item:last-child {
  border-bottom: none;
}

.trending-item:hover {
  background: var(--color-bg);
}

.item-rank {
  min-width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-bold);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.trending-item:nth-child(1) .item-rank {
  color: #ff4d4f;
}

.trending-item:nth-child(2) .item-rank {
  color: #ff7a45;
}

.trending-item:nth-child(3) .item-rank {
  color: #ffa940;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: var(--font-sm);
  line-height: 1.4;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-meta {
  display: flex;
  gap: var(--spacing-sm);
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
}

.item-hot {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

.item-author {
  color: var(--color-text-placeholder);
}

.show-more-btn {
  width: 100%;
  padding: var(--spacing-sm);
  background: var(--color-bg);
  border: none;
  border-top: 1px solid var(--border-color-light);
  color: var(--color-primary);
  font-size: var(--font-xs);
  cursor: pointer;
  transition: var(--transition);
}

.show-more-btn:hover {
  background: var(--color-bg-secondary);
}

.empty-state-small {
  padding: var(--spacing-md);
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
}
</style>
