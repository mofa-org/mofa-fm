/**
 * 互动相关 API
 */
import client from './client'

export default {
  // 评论列表
  getComments(episodeId) {
    return client.get(`/interactions/episodes/${episodeId}/comments/`)
  },

  // 创建评论
  createComment(data) {
    return client.post('/interactions/comments/create/', data)
  },

  // 删除评论
  deleteComment(commentId) {
    return client.delete(`/interactions/comments/${commentId}/delete/`)
  },

  // 切换点赞
  toggleLike(episodeId) {
    return client.post(`/interactions/episodes/${episodeId}/like/`)
  },

  // 切换关注
  toggleFollow(showId) {
    return client.post(`/interactions/shows/${showId}/follow/`)
  },

  // 我的关注列表
  getMyFollowing(params) {
    return client.get('/interactions/following/', { params })
  },

  // 更新播放进度
  updatePlayProgress(data) {
    return client.post('/interactions/play/update/', data)
  },

  // 我的播放历史
  getMyPlayHistory(params) {
    return client.get('/interactions/play/history/', { params })
  },

  // 继续收听
  getContinueListening() {
    return client.get('/interactions/play/continue/')
  }
}
