import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：附带 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function pickMessage(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (data.msg) return data.msg
  if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg).join('; ')
  if (data.detail) return String(data.detail)
  return ''
}

// 响应拦截：统一错误提示 + 401 跳登录
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const message = pickMessage(error.response?.data) || error.message || '网络错误'

    // 4xx 直接提示；5xx 最多自动重试 2 次
    const config = error.config
    if (status >= 500 && config && !config._retryCount) {
      config._retryCount = 0
    }
    if (status >= 500 && config && config._retryCount < 2) {
      config._retryCount += 1
      return new Promise((resolve) => setTimeout(resolve, 400 * config._retryCount)).then(() =>
        request(config)
      )
    }

    if (status === 401) {
      localStorage.removeItem('token')
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
      ElMessage.error(message || '登录已过期，请重新登录')
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default request
