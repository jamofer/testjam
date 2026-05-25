import { api } from './client'

export const aboutApi = {
  get: () => api.get('/about').then(r => r.data),
}
