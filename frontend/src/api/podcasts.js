/**
 * 播客相关 API
 */
import client from './client'

export default {
  // 分类
  getCategories() {
    return client.get('/podcasts/categories/')
  },

  // 标签
  getTags(params) {
    return client.get('/podcasts/tags/', { params })
  },

  // 播客节目列表
  getShows(params) {
    return client.get('/podcasts/shows/', { params })
  },

  // 播客节目详情
  getShow(slug) {
    return client.get(`/podcasts/shows/${slug}/`)
  },

  // 创建播客节目
  createShow(data) {
    return client.post('/podcasts/shows/create/', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 更新播客节目
  updateShow(slug, data) {
    return client.put(`/podcasts/shows/${slug}/update/`, data)
  },

  // 删除播客节目
  deleteShow(slug) {
    return client.delete(`/podcasts/shows/${slug}/delete/`)
  },

  // 单集列表
  getEpisodes(params) {
    return client.get('/podcasts/episodes/', { params })
  },

  // 单集详情
  getEpisode(showSlug, episodeSlug) {
    return client.get(`/podcasts/shows/${showSlug}/episodes/${episodeSlug}/`)
  },

  // 上传单集
  createEpisode(data) {
    return client.post('/podcasts/episodes/create/', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // AI 生成单集
  generateEpisode(data) {
    return client.post('/podcasts/episodes/generate/', data)
  },

  // RSS 生成单集
  generateEpisodeFromRSS(data) {
    return client.post('/podcasts/episodes/generate-from-rss/', data)
  },

  // 更新单集
  updateEpisode(episodeId, data) {
    return client.put(`/podcasts/episodes/${episodeId}/update/`, data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 删除单集
  deleteEpisode(episodeId) {
    return client.delete(`/podcasts/episodes/${episodeId}/delete/`)
  },

  // 我的播客节目
  getMyShows() {
    return client.get('/podcasts/creator/shows/')
  },

  // 节目的所有单集
  getShowEpisodes(showId) {
    return client.get(`/podcasts/creator/shows/${showId}/episodes/`)
  },

  // 平台统计
  getStats() {
    return client.get('/podcasts/stats/')
  },

  // AI 脚本创作会话
  getGenerationQueue(params) {
    return client.get('/podcasts/creator/generation-queue/', { params })
  },

  getScriptSessions(params) {
    return client.get('/podcasts/script-sessions/', { params })
  },

  getScriptSession(id) {
    return client.get(`/podcasts/script-sessions/${id}/`)
  },

  createScriptSession(data) {
    return client.post('/podcasts/script-sessions/', data)
  },

  updateScriptSession(id, data) {
    return client.put(`/podcasts/script-sessions/${id}/`, data)
  },

  deleteScriptSession(id) {
    return client.delete(`/podcasts/script-sessions/${id}/`)
  },

  // AI 对话
  chatWithAI(sessionId, message) {
    return client.post(`/podcasts/script-sessions/${sessionId}/chat/`, { message })
  },

  // 上传参考文件
  uploadReference(sessionId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/podcasts/script-sessions/${sessionId}/upload_file/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 删除参考文件
  deleteReference(sessionId, fileId) {
    return client.delete(`/podcasts/script-sessions/${sessionId}/delete_file/${fileId}/`)
  },

  // 热搜榜
  getTrendingSources() {
    return client.get('/podcasts/trending/sources/')
  },

  getTrendingData(source) {
    return client.get(`/podcasts/trending/${source}/`)
  },

  // Debate/Conference 生成
  generateDebate(data) {
    return client.post('/podcasts/episodes/generate-debate/', data)
  },

  // 获取Episode详情（by ID）
  getEpisodeById(episodeId) {
    return client.get(`/podcasts/episodes/${episodeId}/`)
  },

  // 为Debate/Conference生成音频
  generateDebateAudio(episodeId, showId) {
    return client.post(`/podcasts/episodes/${episodeId}/generate-audio/`, { show_id: showId })
  },

  // 获取我的辩论历史
  getMyDebates() {
    return client.get('/podcasts/debates/')
  }
}
