// ========================================
// Axios 实例配置
// 作用：所有 API 请求都走这里，统一处理 token、错误、重试
// ========================================

import axios from 'axios'

// 创建一个 axios 实例（不要用全局 axios）
const api = axios.create({
  // baseURL：所有请求都会自动加 /api 前缀
  // 比如 api.post('/auth/token/') 实际发到 /api/auth/token/
  baseURL: '/api',
  
  // timeout：请求 10 秒没响应就报超时
  timeout: 10000,
})

// ========================================
// 【第一部分】请求拦截器
// 作用：每次发请求之前自动执行，用来给请求加 token
// ========================================
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 读取 access token
    const token = localStorage.getItem('access_token')
    
    // 如果有 token，加到请求头
    // 格式：Authorization: Bearer eyJhbGciOi...
    // 这是 JWT 认证的标准格式，后端会解析这个头
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 返回 config，让请求继续
    return config
  },
  (error) => {
    // 请求还没发出去就出错（很少见，比如配置错了）
    return Promise.reject(error)
  }
)

// ========================================
// 【第二部分】响应拦截器
// 作用：处理响应和错误
// ========================================

// ---------- 2.1 刷新 token 用的状态变量 ----------
// 防止多个请求同时触发多次刷新
let isRefreshing = false

// 把刷新期间收到的新请求挂起，等 token 刷新完再重发
let pendingRequests = []

// ---------- 2.2 响应拦截器主逻辑 ----------
api.interceptors.response.use(
  // 【成功分支】状态码 2xx，直接返回响应
  (response) => response,

  // 【失败分支】状态码不是 2xx，进入这里
  async (error) => {
    // originalRequest 是这次失败请求的配置（包含 url、method、headers 等）
    const originalRequest = error.config

    // ==========================================
    // 情况 1：不是 401，或者这个请求已经重试过了
    // → 直接抛错，不再处理
    // ==========================================
    if (!error.response || error.response.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    // ==========================================
    // 情况 2：刷新 token 接口本身就失败了
    // → 说明 refresh token 也过期了，直接踢回登录页
    // ==========================================
    if (originalRequest.url?.includes('/auth/token/refresh/')) {
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // ==========================================
    // 情况 3：正在刷新 token 时，其他请求又收到 401
    // → 把当前请求挂起，等刷新完成后再重发
    // ==========================================
    if (isRefreshing) {
      return new Promise((resolve) => {
        pendingRequests.push((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          resolve(api(originalRequest))
        })
      })
    }

    // ==========================================
    // 情况 4：开始刷新流程
    // ==========================================
    originalRequest._retry = true  // 标记这个请求已经重试过
    isRefreshing = true

    // 从 localStorage 拿 refresh token
    const refreshToken = localStorage.getItem('refresh_token')

    // 没有 refresh token → 没救了，踢回登录
    if (!refreshToken) {
      localStorage.clear()
      window.location.href = '/login'
      isRefreshing = false
      return Promise.reject(error)
    }

    try {
      // 用 refresh token 换新的 access token
      // 注意：这里用全局 axios，不是 api 实例，避免死循环
      const res = await axios.post('/api/auth/token/refresh/', {
        refresh: refreshToken,
      })

      const newAccess = res.data.access

      // 保存新的 access token
      localStorage.setItem('access_token', newAccess)

      // 重发所有被挂起的请求
      pendingRequests.forEach((callback) => callback(newAccess))
      pendingRequests = []

      // 重发原请求（用新 token）
      originalRequest.headers.Authorization = `Bearer ${newAccess}`
      return api(originalRequest)
    } catch (refreshError) {
      // 刷新失败，清空所有登录状态，踢回登录页
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      // 无论如何，结束刷新状态
      isRefreshing = false
    }
  }
)

export default api