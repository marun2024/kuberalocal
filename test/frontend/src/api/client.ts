import axios from 'axios'
import logger from '../utils/logger'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Check if JWT is expired
const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000 // Convert to milliseconds
    return Date.now() >= exp
  } catch {
    return true
  }
}

// Add auth token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  logger.debug('API Request', {
    method: config.method?.toUpperCase(),
    url: config.url,
    hasToken: !!token,
  })

  if (token) {
    // Check token expiration before adding to request
    if (isTokenExpired(token)) {
      logger.debug('Token expired during request, removing and redirecting')
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(new Error('Token expired'))
    }
    config.headers.Authorization = `Bearer ${token}`
    logger.debug('Auth header added to request')
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    logger.error('API Error', { error: error })

    // Handle 401 errors by redirecting to login
    if (error.response?.status === 401) {
      logger.debug('401 error, clearing token and redirecting to login')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export default apiClient
