import { describe, it, expect, beforeEach, afterEach } from 'vitest'

import { api, REQUEST_TIMEOUT_MS, TRANSFER_TIMEOUT_MS } from '../api/client'

let sentConfig

beforeEach(() => {
  sentConfig = null
  api.defaults.adapter = (config) => {
    sentConfig = config
    return Promise.resolve({ data: {}, status: 200, statusText: 'OK', headers: {}, config })
  }
})

afterEach(() => {
  delete api.defaults.adapter
})

describe('api client timeouts', () => {
  it('gives up on ordinary requests after the request timeout', async () => {
    await api.get('/projects')

    expect(sentConfig.timeout).toBe(REQUEST_TIMEOUT_MS)
  })

  it('allows uploads the longer transfer timeout', async () => {
    await api.post('/cases/1/attachments', new FormData())

    expect(sentConfig.timeout).toBe(TRANSFER_TIMEOUT_MS)
  })

  it('allows downloads the longer transfer timeout', async () => {
    await api.get('/projects/1/export', { responseType: 'blob' })

    expect(sentConfig.timeout).toBe(TRANSFER_TIMEOUT_MS)
  })

  it('keeps a timeout set explicitly by the caller', async () => {
    await api.get('/projects/1/export', { responseType: 'blob', timeout: 5_000 })

    expect(sentConfig.timeout).toBe(5_000)
  })
})
