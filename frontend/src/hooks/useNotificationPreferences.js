import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notificationPreferencesApi } from '../api/notificationPreferences'

const PREFS_KEY = ['notification-preferences']

export function useNotificationPreferences() {
  return useQuery({
    queryKey: PREFS_KEY,
    queryFn: notificationPreferencesApi.list,
  })
}

export function useUpdateNotificationPreference() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ eventType, in_app, email }) =>
      notificationPreferencesApi.update(eventType, { in_app, email }),
    onSuccess: (updated) => {
      queryClient.setQueryData(PREFS_KEY, (previous = []) => {
        const without = previous.filter(p => p.event_type !== updated.event_type)
        return [...without, updated]
      })
    },
  })
}
