/**
 * 用户认证 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isAuthenticated = computed(() => !!accessToken.value)
  const isCreator = computed(() => user.value?.is_creator || false)

  // 登录
  async function login(credentials) {
    const data = await api.auth.login(credentials)
    setAuth(data)
    return data
  }

  // 注册
  async function register(userData) {
    const data = await api.auth.register(userData)
    setAuth(data)
    return data
  }

  // 设置认证信息
  function setAuth(data) {
    user.value = data.user
    accessToken.value = data.tokens.access
    refreshToken.value = data.tokens.refresh

    localStorage.setItem('access_token', data.tokens.access)
    localStorage.setItem('refresh_token', data.tokens.refresh)
  }

  // 登出
  function logout() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // 获取当前用户信息
  async function fetchCurrentUser() {
    if (!accessToken.value) return

    try {
      const data = await api.auth.getCurrentUser()
      user.value = data
      return data
    } catch (error) {
      // Token 无效，清除
      logout()
      throw error
    }
  }

  // 更新用户资料
  async function updateProfile(userData) {
    const data = await api.auth.updateProfile(userData)
    user.value = { ...user.value, ...data }
    return data
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isCreator,
    login,
    register,
    logout,
    fetchCurrentUser,
    updateProfile
  }
})
