import { api } from './client'

const BASE = '/users/me/notification-preferences'

export const notificationPreferencesApi = {
  list: () => api.get(BASE).then(r => r.data),
  update: (eventType, body) =>
    api.put(`${BASE}/${eventType}`, body).then(r => r.data),
}
