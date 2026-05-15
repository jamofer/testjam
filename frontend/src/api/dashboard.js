import { api } from './client'

export const dashboardApi = {
  get: (projectId, { range = 30, cards } = {}) => {
    const params = { range }
    if (cards) params.cards = cards.join(',')
    return api.get(`/projects/${projectId}/dashboard`, { params }).then(r => r.data)
  },
}
