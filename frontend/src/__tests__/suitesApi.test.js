import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('../api/client', () => ({
  api: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve()),
  },
}))

import { api } from '../api/client'
import { suitesApi } from '../api/testcases'

beforeEach(() => vi.clearAllMocks())

describe('suitesApi.listChildren', () => {
  it('sends parent_suite_id as a query param', async () => {
    await suitesApi.listChildren(3, 7)
    expect(api.get).toHaveBeenCalledWith('/projects/3/suites', {
      params: { parent_suite_id: 7 },
    })
  })

  it('uses the correct project id in the URL', async () => {
    await suitesApi.listChildren(42, 1)
    const [url] = api.get.mock.calls[0]
    expect(url).toBe('/projects/42/suites')
  })
})

describe('suitesApi.list (root suites)', () => {
  it('does not send parent_suite_id', async () => {
    await suitesApi.list(5)
    expect(api.get).toHaveBeenCalledWith('/projects/5/suites')
  })
})
