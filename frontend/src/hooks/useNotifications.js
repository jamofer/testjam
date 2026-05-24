import { useMemo } from 'react'
import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '../api/notifications'
import { authApi } from '../api/auth'
import { useTopicSocket } from './useTopicSocket'

const LIST_KEY = ['notifications']
const COUNT_KEY = ['notifications', 'unread-count']
const PAGE_SIZE = 50

export function useNotifications() {
  return useInfiniteQuery({
    queryKey: LIST_KEY,
    queryFn: ({ pageParam = 0 }) =>
      notificationsApi.list({ skip: pageParam, limit: PAGE_SIZE }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length < PAGE_SIZE ? undefined : allPages.length * PAGE_SIZE,
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: COUNT_KEY,
    queryFn: notificationsApi.unreadCount,
    refetchOnWindowFocus: true,
  })
}

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY })
      qc.invalidateQueries({ queryKey: COUNT_KEY })
    },
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY })
      qc.invalidateQueries({ queryKey: COUNT_KEY })
    },
  })
}

export function useNotificationsSocket(enabled) {
  const qc = useQueryClient()
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    enabled: !!enabled,
    retry: false,
    staleTime: Infinity,
  })

  const topics = useMemo(() => (me ? [`user:${me.id}`] : []), [me])
  const handlers = useMemo(() => ({
    notification: (data) => {
      if (!data) return
      qc.setQueryData(LIST_KEY, (prev) => {
        if (!prev?.pages?.length) {
          return { pages: [[data]], pageParams: [0] }
        }
        const [firstPage, ...rest] = prev.pages
        return { ...prev, pages: [[data, ...firstPage], ...rest] }
      })
      qc.setQueryData(COUNT_KEY, (prev = { unread: 0 }) => ({ unread: (prev?.unread ?? 0) + 1 }))
    },
  }), [qc])

  useTopicSocket(topics, handlers, { enabled: !!enabled && !!me })
}
