/**
 * 认证相关 API
 */
import client from './client'

export default {
  // 注册
  register(data) {
    return client.post('/auth/register/', data)
  },

  // 登录
  login(data) {
    return client.post('/auth/login/', data)
  },

  // 获取当前用户信息
  getCurrentUser() {
    return client.get('/auth/me/')
  },

  // 更新用户资料
  updateProfile(data) {
    return client.put('/auth/me/update/', data)
  },

  // 申请成为创作者
  becomeCreator() {
    return client.post('/auth/creator/become/')
  },

  // 验证创作者答案
  verifyCreator(data) {
    return client.post('/auth/creator/verify/', data)
  }
}
