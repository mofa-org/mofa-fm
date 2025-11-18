/**
 * 搜索相关 API
 */
import client from './client'

export default {
  // 全局搜索
  search(query) {
    return client.get('/search/', { params: { q: query } })
  },

  // 快速搜索（自动完成）
  quickSearch(query) {
    return client.get('/search/quick/', { params: { q: query } })
  }
}
