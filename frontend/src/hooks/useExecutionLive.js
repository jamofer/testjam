import { useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTopicSocket } from './useTopicSocket'

export function useExecutionLive(executionId, { enabled = true } = {}) {
  const queryClient = useQueryClient()

  const topics = useMemo(
    () => (executionId ? [`execution:${executionId}`] : []),
    [executionId],
  )

  const handlers = useMemo(() => ({
    "execution.updated": (data) => {
      if (!data?.id) return
      queryClient.setQueryData(["executions", String(data.id)], data)
    },
    "result.updated": (data) => {
      if (!data?.id) return
      patchResult(queryClient, executionId, data)
    },
    "result.started": (data) => {
      if (!data?.id) return
      patchResult(queryClient, executionId, data)
    },
    "result.finished": (data) => {
      if (!data?.id) return
      patchResult(queryClient, executionId, data)
    },
    "step_result.started": (data) => {
      if (!data) return
      patchStepResult(queryClient, executionId, data)
    },
    "step_result.finished": (data) => {
      if (!data) return
      patchStepResult(queryClient, executionId, data)
    },
    "step_result.log_appended": (data) => {
      const entries = extractLogEntries(data)
      if (entries.length === 0) return
      appendStepResultLogs(queryClient, executionId, entries)
    },
  }), [queryClient, executionId])

  return useTopicSocket(topics, handlers, { enabled })
}

function patchResult(queryClient, executionId, incoming) {
  queryClient.setQueryData(["results", String(executionId)], (previous = []) => {
    if (!Array.isArray(previous)) return previous
    if (!previous.some(result => result.id === incoming.id)) {
      return [...previous, incoming]
    }
    return previous.map(result =>
      result.id === incoming.id ? { ...result, ...incoming } : result,
    )
  })
}

function patchStepResult(queryClient, executionId, incoming) {
  const targetResultId = incoming.test_result_id
  queryClient.setQueryData(["results", String(executionId)], (previous = []) => {
    if (!Array.isArray(previous)) return previous
    return previous.map(result => {
      if (result.id !== targetResultId) return result
      const stepResults = result.step_results ?? []
      const exists = stepResults.some(stepResult => stepResult.id === incoming.id)
      const nextStepResults = exists
        ? stepResults.map(stepResult =>
            stepResult.id === incoming.id ? { ...stepResult, ...incoming } : stepResult,
          )
        : [...stepResults, incoming]
      return { ...result, step_results: nextStepResults }
    })
  })
}

function extractLogEntries(data) {
  if (!data) return []
  if (Array.isArray(data.entries)) return data.entries
  if (data.step_result_id != null) return [data]
  return []
}

function appendStepResultLogs(queryClient, executionId, entries) {
  const byStepResultId = groupEntriesByStepResultId(entries)
  queryClient.setQueryData(["results", String(executionId)], (previous = []) => {
    if (!Array.isArray(previous)) return previous
    return previous.map(result => mergeLogEntries(result, byStepResultId))
  })
}

function groupEntriesByStepResultId(entries) {
  const grouped = new Map()
  for (const entry of entries) {
    if (entry?.step_result_id == null) continue
    const list = grouped.get(entry.step_result_id) ?? []
    list.push(entry)
    grouped.set(entry.step_result_id, list)
  }
  return grouped
}

function mergeLogEntries(result, byStepResultId) {
  const stepResults = result.step_results ?? []
  let touched = false
  const nextStepResults = stepResults.map(stepResult => {
    const entriesForStep = byStepResultId.get(stepResult.id)
    if (!entriesForStep) return stepResult
    touched = true
    return {
      ...stepResult,
      log_output: entriesForStep.reduce(
        (acc, entry) => appendLogLine(acc, entry.level, entry.message),
        stepResult.log_output,
      ),
    }
  })
  return touched ? { ...result, step_results: nextStepResults } : result
}

function appendLogLine(existing, level, message) {
  const entry = `**[${level}]** ${message}`
  return existing ? `${existing}\n\n${entry}` : entry
}
