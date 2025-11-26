/**
 * 搜索相关 API
 */
import client from './client'

export default {
  // 全局搜索
  search(params) {
    return client.get('/search/', { params })
  },

  // 快速搜索（自动完成）
  quickSearch(query) {
    return client.get('/search/quick/', { params: { q: query } })
  },

  // 获取搜索历史
  getSearchHistory(limit = 10) {
    return client.get('/search/history/', { params: { limit } })
  },

  // 清空搜索历史
  clearSearchHistory() {
    return client.delete('/search/history/clear/')
  },

  // 获取热门搜索
  getPopularSearches(limit = 10) {
    return client.get('/search/popular/', { params: { limit } })
  },

  // 获取搜索建议（混合历史和热门）
  getSearchSuggestions(query = '', limit = 10) {
    return client.get('/search/suggestions/', { params: { q: query, limit } })
  }
}
