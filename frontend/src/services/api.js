import axios from 'axios'

const configuredApiUrl = import.meta.env.VITE_API_URL || ''
const apiHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const baseURL = configuredApiUrl && !/^https?:\/\/localhost(?::\d+)?$/i.test(configuredApiUrl)
  ? configuredApiUrl
  : (configuredApiUrl ? configuredApiUrl.replace('localhost', apiHost) : '')

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api

export function getApiErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((item) => item.msg || item.message)
      .filter(Boolean)
      .join('. ') || fallbackMessage
  }

  if (error.code === 'ERR_NETWORK') {
    return 'Unable to reach the server. Please try again in a moment.'
  }

  return fallbackMessage
}
