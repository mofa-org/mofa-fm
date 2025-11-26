<template>
  <div class="search-page">
    <div class="container">
      <!-- 搜索框 -->
      <div class="search-header">
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索播客、单集、评论..."
            size="large"
            clearable
            @keyup.enter="handleSearch"
            @input="handleInputChange"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="large" class="search-btn" @click="handleSearch">
            搜索
          </el-button>
        </div>

        <!-- 搜索建议下拉 -->
        <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-dropdown mofa-card">
          <div
            v-for="(suggestion, index) in suggestions"
            :key="index"
            class="suggestion-item"
            @click="selectSuggestion(suggestion.query)"
          >
            <el-icon v-if="suggestion.type === 'history'" class="suggestion-icon">
              <Clock />
            </el-icon>
            <el-icon v-else class="suggestion-icon">
              <TrendCharts />
            </el-icon>
            <span class="suggestion-text">{{ suggestion.query }}</span>
            <span v-if="suggestion.count" class="suggestion-count">{{ suggestion.count }}</span>
          </div>
        </div>
      </div>

      <!-- 热门搜索 -->
      <div v-if="!query && popularSearches.length > 0" class="popular-section">
        <h3 class="popular-title">热门搜索</h3>
        <div class="popular-tags">
          <span
            v-for="(item, index) in popularSearches"
            :key="index"
            class="mofa-tag popular-tag"
            @click="selectSuggestion(item.query)"
          >
            <span class="tag-index" :class="{ 'top-three': index < 3 }">{{ index + 1 }}</span>
            {{ item.query }}
          </span>
        </div>
      </div>

      <!-- 高级过滤器 -->
      <div v-if="query" class="filters-section">
        <div class="filters-row">
          <el-select v-model="filters.type" placeholder="类型" @change="handleSearch" clearable>
            <el-option label="全部" value="all" />
            <el-option label="节目" value="show" />
            <el-option label="单集" value="episode" />
            <el-option label="评论" value="comment" />
          </el-select>

          <el-select
            v-model="filters.category"
            placeholder="分类"
            @change="handleSearch"
            clearable
            v-show="false"
          >
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>

          <el-select v-model="filters.sort" placeholder="排序" @change="handleSearch">
            <el-option label="相关度" value="relevance" />
            <el-option label="最新发布" value="date" />
            <el-option label="最受欢迎" value="popularity" />
          </el-select>

          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
            clearable
          />

          <el-button
            v-if="hasActiveFilters"
            link
            type="primary"
            @click="clearFilters"
          >
            清空筛选
          </el-button>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="query && !loading">
        <div class="results-header">
          <h2 class="results-title">
            找到 <span class="highlight-number">{{ results.total }}</span> 条结果
          </h2>
        </div>

        <!-- 播客节目 -->
        <section v-if="results.shows?.length > 0" class="section">
          <h3 class="section-title">播客节目 ({{ results.shows.length }})</h3>
          <div class="shows-grid">
            <ShowCard v-for="show in results.shows" :key="show.id" :show="show" />
          </div>
        </section>

        <!-- 单集 -->
        <section v-if="results.episodes?.length > 0" class="section">
          <h3 class="section-title">单集 ({{ results.episodes.length }})</h3>
          <div class="episodes-list">
            <EpisodeCard
              v-for="episode in results.episodes"
              :key="episode.id"
              :episode="episode"
              :playlist="results.episodes"
            >
              <template #description>
                <div
                  class="episode-excerpt"
                  v-html="highlightExcerpt(episode.description, query)"
                ></div>
              </template>
            </EpisodeCard>
          </div>
        </section>

        <!-- 评论 -->
        <section v-if="results.comments?.length > 0" class="section">
          <h3 class="section-title">评论 ({{ results.comments.length }})</h3>
          <div class="comments-list">
            <div v-for="comment in results.comments" :key="comment.id" class="comment-item mofa-card">
              <p class="comment-text" v-html="highlightExcerpt(comment.text, query, 80)"></p>
              <div class="comment-meta">
                <span class="comment-author">{{ comment.user.username }}</span>
                <span class="comment-separator">·</span>
                <router-link
                  :to="`/shows/${comment.episode.show.slug}/episodes/${comment.episode.slug}`"
                  class="comment-link"
                >
                  {{ comment.episode.title }}
                </router-link>
              </div>
            </div>
          </div>
        </section>

        <el-empty v-if="results.total === 0" description="没有找到相关结果">
          <el-button type="primary" @click="clearFilters">清空筛选条件</el-button>
        </el-empty>
      </div>

      <!-- 加载中 -->
      <div v-else-if="loading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>搜索中...</p>
      </div>

      <!-- 初始状态（搜索历史） -->
      <div v-else-if="searchHistory.length > 0" class="history-section">
        <div class="history-header">
          <h3 class="history-title">搜索历史</h3>
          <el-button link type="primary" @click="handleClearHistory">清空</el-button>
        </div>
        <div class="history-list">
          <div
            v-for="(item, index) in searchHistory"
            :key="index"
            class="history-item"
            @click="selectSuggestion(item.query)"
          >
            <el-icon class="history-icon"><Clock /></el-icon>
            <span class="history-text">{{ item.query }}</span>
            <el-icon class="history-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  Loading,
  Clock,
  TrendCharts,
  ArrowRight
} from '@element-plus/icons-vue'
import api from '@/api'
import ShowCard from '@/components/podcast/ShowCard.vue'
import EpisodeCard from '@/components/podcast/EpisodeCard.vue'
import { highlightExcerpt } from '@/utils/highlight'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const query = ref('')
const results = ref({})
const loading = ref(false)
const suggestions = ref([])
const showSuggestions = ref(false)
const popularSearches = ref([])
const searchHistory = ref([])
const categories = ref([])
const dateRange = ref(null)

const filters = ref({
  type: 'all',
  category: null,
  sort: 'relevance'
})

const hasActiveFilters = computed(() => {
  return (
    filters.value.type !== 'all' ||
    filters.value.category ||
    filters.value.sort !== 'relevance' ||
    dateRange.value
  )
})

let suggestionTimer = null

onMounted(async () => {
  query.value = route.query.q || ''
  searchQuery.value = query.value

  // 加载分类
  await loadCategories()

  // 加载热门搜索和搜索历史
  await Promise.all([loadPopularSearches(), loadSearchHistory()])

  if (query.value) {
    // 从 URL 恢复过滤器
    if (route.query.type) filters.value.type = route.query.type
    if (route.query.category) filters.value.category = parseInt(route.query.category)
    if (route.query.sort) filters.value.sort = route.query.sort
    if (route.query.date_from && route.query.date_to) {
      dateRange.value = [route.query.date_from, route.query.date_to]
    }

    await performSearch()
  }
})

// 监听路由变化
watch(
  () => route.query.q,
  (newQuery) => {
    if (newQuery !== query.value) {
      query.value = newQuery || ''
      searchQuery.value = newQuery || ''
      if (newQuery) {
        performSearch()
      }
    }
  }
)

async function loadCategories() {
  try {
    const data = await api.podcasts.getCategories()
    categories.value = data.results || data
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

async function loadPopularSearches() {
  try {
    const data = await api.search.getPopularSearches(8)
    popularSearches.value = data.results || []
  } catch (error) {
    console.error('加载热门搜索失败:', error)
  }
}

async function loadSearchHistory() {
  try {
    const data = await api.search.getSearchHistory(10)
    searchHistory.value = data.results || []
  } catch (error) {
    console.error('加载搜索历史失败:', error)
  }
}

async function loadSuggestions() {
  try {
    const data = await api.search.getSearchSuggestions(searchQuery.value, 8)
    suggestions.value = data.results || []
    showSuggestions.value = suggestions.value.length > 0
  } catch (error) {
    console.error('加载搜索建议失败:', error)
  }
}

function handleInputChange() {
  // 防抖加载建议
  clearTimeout(suggestionTimer)
  if (searchQuery.value.trim().length >= 2) {
    suggestionTimer = setTimeout(() => {
      loadSuggestions()
    }, 300)
  } else {
    suggestions.value = []
    showSuggestions.value = false
  }
}

function selectSuggestion(suggestionQuery) {
  searchQuery.value = suggestionQuery
  showSuggestions.value = false
  handleSearch()
}

function handleSearch() {
  query.value = searchQuery.value.trim()
  showSuggestions.value = false

  if (!query.value || query.value.length < 2) {
    ElMessage.warning('请输入至少2个字符')
    return
  }

  // 更新 URL
  const queryParams = { q: query.value }
  if (filters.value.type !== 'all') queryParams.type = filters.value.type
  if (filters.value.category) queryParams.category = filters.value.category
  if (filters.value.sort !== 'relevance') queryParams.sort = filters.value.sort
  if (dateRange.value) {
    queryParams.date_from = dateRange.value[0]
    queryParams.date_to = dateRange.value[1]
  }

  router.push({ query: queryParams })
  performSearch()
}

async function performSearch() {
  loading.value = true
  try {
    const params = {
      q: query.value,
      type: filters.value.type,
      sort: filters.value.sort
    }

    if (filters.value.category) {
      params.category = filters.value.category
    }

    if (dateRange.value) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }

    results.value = await api.search.search(params)
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
    console.error('搜索失败:', error)
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  handleSearch()
}

function clearFilters() {
  filters.value = {
    type: 'all',
    category: null,
    sort: 'relevance'
  }
  dateRange.value = null
  handleSearch()
}

async function handleClearHistory() {
  try {
    await api.search.clearSearchHistory()
    searchHistory.value = []
    ElMessage.success('搜索历史已清空')
  } catch (error) {
    ElMessage.error('清空失败')
  }
}

// 点击外部关闭建议框
document.addEventListener('click', (e) => {
  if (!e.target.closest('.search-box')) {
    showSuggestions.value = false
  }
})
</script>

<style scoped>
.search-page {
  padding: var(--spacing-xl) 0;
  min-height: 80vh;
}

/* 搜索头部 */
.search-header {
  position: relative;
  margin-bottom: var(--spacing-2xl);
}

.search-box {
  display: flex;
  gap: var(--spacing-md);
  max-width: 800px;
  margin: 0 auto;
}

.search-box :deep(.el-input) {
  flex: 1;
}

.search-box :deep(.el-input__wrapper) {
  border: 2px solid var(--color-border);
  border-radius: var(--radius-default);
  transition: all 0.2s;
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.08);
}

.search-box :deep(.el-input__wrapper:focus),
.search-box :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow: 4px 4px 0 rgba(255, 81, 59, 0.15);
  transform: translate(-1px, -1px);
}

.search-btn {
  min-width: 100px;
  font-weight: var(--font-semibold);
  box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.12);
  transition: all 0.2s;
}

.search-btn:hover {
  transform: translate(-2px, -2px);
  box-shadow: 5px 5px 0 rgba(0, 0, 0, 0.18);
}

.search-btn:active {
  transform: translate(0, 0);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.12);
}

/* 搜索建议 */
.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 100px;
  margin: var(--spacing-sm) auto 0;
  max-width: 800px;
  z-index: 1000;
  max-height: 400px;
  overflow-y: auto;
  border: 2px solid var(--color-border);
  box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.12);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border-left: 3px solid transparent;
}

.suggestion-item:hover {
  background-color: var(--color-bg-secondary);
  padding-left: calc(var(--spacing-md) + 3px);
}

.suggestion-item:nth-child(4n+1):hover {
  border-left-color: var(--color-primary);
}

.suggestion-item:nth-child(4n+2):hover {
  border-left-color: var(--color-accent);
}

.suggestion-item:nth-child(4n+3):hover {
  border-left-color: var(--color-warning);
}

.suggestion-item:nth-child(4n+4):hover {
  border-left-color: var(--color-success);
}

.suggestion-icon {
  color: var(--color-text-tertiary);
  font-size: 16px;
  transition: color 0.2s;
}

.suggestion-item:nth-child(4n+1):hover .suggestion-icon {
  color: var(--color-primary);
}

.suggestion-item:nth-child(4n+2):hover .suggestion-icon {
  color: var(--color-accent);
}

.suggestion-item:nth-child(4n+3):hover .suggestion-icon {
  color: var(--color-warning);
}

.suggestion-item:nth-child(4n+4):hover .suggestion-icon {
  color: var(--color-success);
}

.suggestion-text {
  flex: 1;
  color: var(--color-text-primary);
}

.suggestion-count {
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
  padding: 2px 8px;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  font-weight: var(--font-medium);
}

/* 热门搜索 */
.popular-section {
  margin-bottom: var(--spacing-2xl);
}

.popular-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.popular-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.popular-tag {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  background: white;
  border: 2px solid var(--color-border);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.08);
  transition: all 0.2s;
}

.popular-tag:hover {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.15);
}

.popular-tag:active {
  transform: translate(0, 0);
  box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.08);
}

.popular-tag:nth-child(4n+1) .tag-index {
  background-color: var(--color-primary);
  color: white;
}

.popular-tag:nth-child(4n+2) .tag-index {
  background-color: var(--color-accent);
  color: white;
}

.popular-tag:nth-child(4n+3) .tag-index {
  background-color: var(--color-warning);
  color: var(--color-text-primary);
}

.popular-tag:nth-child(4n+4) .tag-index {
  background-color: var(--color-success);
  color: white;
}

.tag-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: var(--font-bold);
  flex-shrink: 0;
}

/* 过滤器 */
.filters-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: linear-gradient(135deg,
    rgba(255, 81, 59, 0.05) 0%,
    rgba(253, 85, 63, 0.05) 25%,
    rgba(255, 198, 62, 0.05) 50%,
    rgba(109, 202, 208, 0.05) 100%);
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  background-clip: padding-box;
  position: relative;
}

.filters-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-bar);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.filters-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  align-items: center;
}

.filters-row :deep(.el-select),
.filters-row :deep(.el-date-editor) {
  min-width: 150px;
}

/* 结果头部 */
.results-header {
  margin-bottom: var(--spacing-lg);
}

.results-title {
  font-size: var(--font-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.highlight-number {
  color: var(--color-primary);
  font-weight: var(--font-bold);
}

/* 分区 */
.section {
  margin-bottom: var(--spacing-2xl);
}

.section-title {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 3px solid transparent;
  background: linear-gradient(to right, var(--gradient-bar)) left bottom / 100% 3px no-repeat;
  position: relative;
  padding-left: var(--spacing-sm);
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 60%;
  background: var(--gradient-bar);
  border-radius: 2px;
}

.shows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.episodes-list,
.comments-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* 评论项 */
.comment-item {
  padding: var(--spacing-md);
  transition: all 0.2s;
}

.comment-text {
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.comment-author {
  font-weight: var(--font-semibold);
}

.comment-separator {
  color: var(--color-text-quaternary);
}

.comment-link {
  color: var(--color-primary);
  text-decoration: none;
}

.comment-link:hover {
  text-decoration: underline;
}

/* 高亮样式 */
:deep(.highlight) {
  background-color: rgba(255, 193, 7, 0.3);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.episode-excerpt {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* 搜索历史 */
.history-section {
  margin-top: var(--spacing-2xl);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.history-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.history-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: white;
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-default);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.history-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--gradient-bar);
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover::before {
  opacity: 1;
}

.history-item:hover {
  border-color: var(--color-primary);
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-md);
}

.history-item:nth-child(4n+1):hover {
  border-color: var(--color-primary);
}

.history-item:nth-child(4n+2):hover {
  border-color: var(--color-accent);
}

.history-item:nth-child(4n+3):hover {
  border-color: var(--color-warning);
}

.history-item:nth-child(4n+4):hover {
  border-color: var(--color-success);
}

.history-icon {
  color: var(--color-text-tertiary);
  font-size: 16px;
}

.history-text {
  flex: 1;
  color: var(--color-text-primary);
}

.history-arrow {
  color: var(--color-text-quaternary);
  font-size: 14px;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: var(--spacing-3xl);
}

.loading .el-icon {
  font-size: 48px;
  background: var(--gradient-bar);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: var(--spacing-md);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.loading p {
  color: var(--color-text-secondary);
  font-size: var(--font-lg);
  font-weight: var(--font-medium);
}

/* 响应式 */
@media (max-width: 768px) {
  .search-box {
    flex-direction: column;
  }

  .search-btn {
    width: 100%;
  }

  .suggestions-dropdown {
    right: 0;
  }

  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filters-row :deep(.el-select),
  .filters-row :deep(.el-date-editor) {
    width: 100%;
  }

  .shows-grid {
    grid-template-columns: 1fr;
  }
}
</style>
