import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证 API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/profile')
}

// 对话 API
export const conversationAPI = {
  create: (data) => api.post('/conversations', data),
  list: () => api.get('/conversations'),
  get: (id) => api.get(`/conversations/${id}`),
  sendMessage: (id, data) => api.post(`/conversations/${id}/messages`, data),
  finalize: (id) => api.post(`/conversations/${id}/finalize`)
}

// 脚本 API
export const scriptAPI = {
  create: (data) => api.post('/scripts', data),
  list: () => api.get('/scripts'),
  get: (id) => api.get(`/scripts/${id}`),
  update: (id, data) => api.put(`/scripts/${id}`, data)
}

// 任务 API
export const taskAPI = {
  create: (data) => api.post('/tasks', data),
  list: () => api.get('/tasks'),
  get: (id) => api.get(`/tasks/${id}`),
  getVoices: () => api.get('/tasks/voices'),
  downloadAudio: (audioId) => `/api/tasks/audios/${audioId}/download`
}

export default api
