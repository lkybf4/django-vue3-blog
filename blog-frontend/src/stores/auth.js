import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  // 登录
  async function login(credentials) {
    try {
      const response = await api.post('/auth/token/', credentials)
      const { access, refresh } = response.data
      
      accessToken.value = access
      refreshToken.value = refresh
      
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
      
      // 获取用户信息
      await fetchUserProfile()
      
      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  // 注册
  async function register(userData) {
    try {
      const response = await api.post('/auth/register/', userData)
      return response.data
    } catch (error) {
      console.error('Register failed:', error)
      throw error
    }
  }

  // 获取用户信息
  async function fetchUserProfile() {
    try {
      const response = await api.get('/auth/profile/')
      user.value = response.data
      return response.data
    } catch (error) {
      console.error('Fetch profile failed:', error)
      throw error
    }
  }

  // 登出
  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    login,
    register,
    fetchUserProfile,
    logout,
  }
})
