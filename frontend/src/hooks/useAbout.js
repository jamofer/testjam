import { useQuery } from '@tanstack/react-query'
import { aboutApi } from '../api/about'

export function useAbout() {
  return useQuery({
    queryKey: ['about'],
    queryFn: aboutApi.get,
    staleTime: Infinity,
  })
}
