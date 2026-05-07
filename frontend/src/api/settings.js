import { api } from './client'

export const settingsApi = {
  public: () => api.get('/settings/public').then(r => r.data),
  read: () => api.get('/settings').then(r => r.data),
  update: (data) => api.put('/settings', data).then(r => r.data),
}
