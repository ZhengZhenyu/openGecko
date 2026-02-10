import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: Add JWT token and community ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Get current community ID from localStorage (only if not already set per-request)
    if (config.headers && !config.headers['X-Community-Id']) {
      const communityId = localStorage.getItem('current_community_id')
      if (communityId) {
        config.headers['X-Community-Id'] = communityId
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor: Handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data as { detail?: string }

      switch (status) {
        case 401:
          // Unauthorized: Clear auth and redirect to login
          localStorage.removeItem('auth_token')
          localStorage.removeItem('current_community_id')
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error(data.detail || '无权限访问')
          break
        case 404:
          ElMessage.error(data.detail || '请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后再试')
          break
        default:
          ElMessage.error(data.detail || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default apiClient
