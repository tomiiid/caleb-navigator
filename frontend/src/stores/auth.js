import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || null)

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(email, password) {
    const res = await api.post('/users/login/', { email, password })
    accessToken.value = res.data.access
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    return res.data
  }

  async function register(email, full_name, password, role) {
    const res = await api.post('/users/register/', { email, full_name, password, role })
    accessToken.value = res.data.access
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    return res.data
  }

  async function fetchUser() {
    try {
      const res = await api.get('/users/me/')
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    accessToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { user, accessToken, isAuthenticated, login, register, fetchUser, logout }
})