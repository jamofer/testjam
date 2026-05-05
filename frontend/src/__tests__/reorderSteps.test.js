import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('../api/client', () => ({
  api: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: [] })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve()),
  },
}))

import { api } from '../api/client'
import { casesApi, suitesApi } from '../api/testcases'

beforeEach(() => vi.clearAllMocks())

describe('casesApi.reorderSteps', () => {
  it('posts step_ids to the correct endpoint', async () => {
    const stepIds = [3, 1, 2]
    await casesApi.reorderSteps(42, stepIds)
    expect(api.post).toHaveBeenCalledWith('/cases/42/steps/reorder', { step_ids: stepIds })
  })
})

describe('suitesApi.reorderSteps', () => {
  it('posts step_ids to the correct endpoint', async () => {
    const stepIds = [5, 6, 4]
    await suitesApi.reorderSteps(7, stepIds)
    expect(api.post).toHaveBeenCalledWith('/suites/7/steps/reorder', { step_ids: stepIds })
  })
})
