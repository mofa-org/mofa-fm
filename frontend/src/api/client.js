/**
 * Axios API 客户端配置
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: '/api',
  timeout: 120000,  // 增加到120秒，支持多轮搜索
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新token
let isRefreshing = false
// 等待token刷新的请求队列
let refreshSubscribers = []

// 通知所有等待的请求使用新token
function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// 添加请求到等待队列
function addRefreshSubscriber(callback) {
  refreshSubscribers.push(callback)
}

// 刷新token
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    throw new Error('No refresh token')
  }

  // 使用新的axios实例避免拦截器循环
  const response = await axios.post('/api/auth/token/refresh/', {
    refresh: refreshToken
  })

  if (response.data && response.data.access) {
    localStorage.setItem('access_token', response.data.access)
    if (response.data.refresh) {
      localStorage.setItem('refresh_token', response.data.refresh)
    }
    return response.data.access
  }
  throw new Error('Invalid refresh response')
}

// 清除认证并跳转登录
function clearAuthAndRedirect() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
  ElMessage.error('登录已过期，请重新登录')
}

// 请求拦截器 - 添加认证token
client.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 如果是FormData，删除Content-Type让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
client.interceptors.response.use(
  response => response.data,
  async error => {
    const originalRequest = error.config

    if (error.response) {
      const { status, data } = error.response

      // 401错误且不是刷新token的请求
      if (status === 401 && originalRequest.url !== '/auth/token/refresh/') {
        const refreshToken = localStorage.getItem('refresh_token')

        // 没有refreshToken（未登录），静默失败不跳转登录页
        if (!refreshToken) {
          console.log('未登录，跳过401处理:', originalRequest.url)
          return Promise.reject(error)
        }

        // 如果正在刷新，等待刷新完成
        if (isRefreshing) {
          return new Promise(resolve => {
            addRefreshSubscriber(newToken => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              resolve(client(originalRequest))
            })
          })
        }

        isRefreshing = true

        try {
          const newToken = await refreshAccessToken()
          isRefreshing = false
          onTokenRefreshed(newToken)

          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return client(originalRequest)
        } catch (refreshError) {
          isRefreshing = false
          refreshSubscribers = []
          clearAuthAndRedirect()
          return Promise.reject(refreshError)
        }
      }

      switch (status) {
        case 400:
          // 验证错误，显示详细信息
          if (data && typeof data === 'object') {
            const errors = Object.values(data).flat()
            if (errors.length > 0) {
              ElMessage.error(errors[0])
            } else {
              ElMessage.error(data.message || data.error || '请求参数错误')
            }
          } else {
            ElMessage.error('请求参数错误')
          }
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          ElMessage.error(data.message || data.error || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查您的连接')
    }

    return Promise.reject(error)
  }
)

export default client
