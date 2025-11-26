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
  error => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 400:
          // 验证错误，显示详细信息
          if (data && typeof data === 'object') {
            // 处理字段级错误
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
        case 401:
          // 未授权，清除token并跳转登录
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          ElMessage.error('请先登录')
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
