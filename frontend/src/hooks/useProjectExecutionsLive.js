import { useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTopicSocket } from './useTopicSocket'

export function useProjectExecutionsLive(projectId, { enabled = true } = {}) {
  const queryClient = useQueryClient()

  const topics = useMemo(
    () => (projectId ? [`project:${projectId}`] : []),
    [projectId],
  )

  const handlers = useMemo(() => ({
    "execution.created": (data) => {
      if (!data?.id) return
      mutateInfinitePages(
        queryClient,
        projectId,
        (page) => page.some(execution => execution.id === data.id)
          ? page
          : [data, ...page],
        { onlyFirstPage: true },
      )
    },
    "execution.updated": (data) => {
      if (!data?.id) return
      mutateInfinitePages(
        queryClient,
        projectId,
        (page) => page.map(execution => execution.id === data.id
          ? { ...execution, ...data }
          : execution),
      )
    },
    "execution.deleted": ({ id } = {}) => {
      if (!id) return
      mutateInfinitePages(
        queryClient,
        projectId,
        (page) => page.filter(execution => execution.id !== id),
      )
    },
  }), [queryClient, projectId])

  return useTopicSocket(topics, handlers, { enabled })
}

function mutateInfinitePages(queryClient, projectId, transform, { onlyFirstPage = false } = {}) {
  queryClient.setQueriesData(
    { queryKey: ["executions", projectId] },
    (oldData) => {
      if (!oldData?.pages) return oldData
      const pages = oldData.pages.map((page, index) => {
        if (onlyFirstPage && index !== 0) return page
        return transform(page)
      })
      return { ...oldData, pages }
    },
  )
}
