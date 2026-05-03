import { api } from './client'

export const authApi = {
  login: (username, password) => {
    const form = new URLSearchParams({ username, password })
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(r => r.data)
  },
  me: () => api.get('/users/me').then(r => r.data),
  updateMe: (data) => api.put('/users/me', data).then(r => r.data),
  changePassword: (data) => api.put('/users/me/password', data),
}
