import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../api/dashboard'

export function useDashboard(projectId, { range = 30 } = {}) {
  return useQuery({
    queryKey: ['dashboard', projectId, { range }],
    queryFn: () => dashboardApi.get(projectId, { range }),
    enabled: !!projectId,
  })
}
