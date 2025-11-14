import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || 'Guest')
  const email = ref(localStorage.getItem('email') || '')
  const creditBalance = ref(parseInt(localStorage.getItem('creditBalance') || '1000'))

  const isLoggedIn = computed(() => !!token.value)

  function setUser(userData) {
    token.value = userData.token ||  token.value
    username.value = userData.username
    email.value = userData.email
    creditBalance.value = userData.creditBalance

    localStorage.setItem('token', token.value)
    localStorage.setItem('username', username.value)
    localStorage.setItem('email', email.value)
    localStorage.setItem('creditBalance', creditBalance.value.toString())
  }

  function logout() {
    token.value = ''
    username.value = 'Guest'
    email.value = ''
    creditBalance.value = 0

    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('email')
    localStorage.removeItem('creditBalance')
  }

  function updateCredit(amount) {
    creditBalance.value += amount
    localStorage.setItem('creditBalance', creditBalance.value.toString())
  }

  return {
    token,
    username,
    email,
    creditBalance,
    isLoggedIn,
    setUser,
    logout,
    updateCredit
  }
})
