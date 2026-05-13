import { api } from './client'

export const RESTORE_CONFIRM_TOKEN = 'I-UNDERSTAND-THIS-REPLACES-ALL-DATA'

function filenameFromResponse(response, fallback) {
  const disposition = response.headers?.['content-disposition'] || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  return match ? match[1] : fallback
}

function downloadResponseAsFile(response, fallbackName) {
  const blob = response.data
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filenameFromResponse(response, fallbackName)
  a.click()
  URL.revokeObjectURL(url)
}

export const settingsApi = {
  public: () => api.get('/settings/public').then(r => r.data),
  read: () => api.get('/settings').then(r => r.data),
  update: (data) => api.put('/settings', data).then(r => r.data),

  downloadBackup: async () => {
    const response = await api.get('/settings/backup', { responseType: 'blob' })
    downloadResponseAsFile(response, 'testjam-backup.zip')
  },

  restoreBackup: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/settings/restore', form, {
      params: { confirm: RESTORE_CONFIRM_TOKEN },
    }).then(r => r.data)
  },
}
