import { api } from '../api/client'

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export async function downloadFromApi(path, filename) {
  const response = await api.get(path, { responseType: 'blob' })
  downloadBlob(response.data, filename)
}
