import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../api/auth'


const TOKEN_KEY = 'token'


// Bind to the browser storage event so a logout in tab A drops the
// cache + redirects tab B immediately, instead of waiting for tab B's
// next request to come back 401. Mounted once by AppLayout so the
// listener exists for the lifetime of an authenticated session.
export function useStorageAuthSync() {
  const queryClient = useQueryClient()
  useEffect(() => {
    const handler = (event) => {
      if (event.key !== TOKEN_KEY) return
      if (event.newValue) return
      if (event.storageArea !== window.localStorage) return
      queryClient.clear()
      window.location.href = '/login'
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [queryClient])
}


export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ username, password }) => authApi.login(username, password),
    onSuccess: (data) => {
      localStorage.setItem(TOKEN_KEY, data.access_token)
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return () => {
    localStorage.removeItem(TOKEN_KEY)
    queryClient.clear()
    window.location.href = '/login'
  }
}

export function useUpdateMe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['me'] }),
  })
}

export function useChangePassword() {
  return useMutation({ mutationFn: authApi.changePassword })
}
