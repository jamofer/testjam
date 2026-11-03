import axios from 'axios'

export const REQUEST_TIMEOUT_MS = 30_000
export const TRANSFER_TIMEOUT_MS = 10 * 60_000

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: REQUEST_TIMEOUT_MS,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.timeout === REQUEST_TIMEOUT_MS && isFileTransfer(config)) {
    config.timeout = TRANSFER_TIMEOUT_MS
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const url = error.config?.url ?? ''
    const isLoginCall = url.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginCall) {
      localStorage.removeItem('token')
      // Soft-navigate via a custom event so the React tree (QueryClient, route
      // state) is preserved instead of paying a full bundle reload.
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    return Promise.reject(error)
  }
)

function isFileTransfer(config) {
  return config.data instanceof FormData || config.responseType === 'blob'
}
