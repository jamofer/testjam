import { useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"

/**
 * Listens for the `auth:unauthorized` event dispatched by the axios
 * interceptor on a 401 and soft-navigates to /login (preserving React state).
 * Also drops the TanStack cache so the next user does not inherit the previous
 * session's data, and listens for cross-tab logout via the `storage` event.
 */
export function AuthRedirector() {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()

  useEffect(() => {
    const goToLogin = () => {
      queryClient.clear()
      if (location.pathname === "/login") return
      navigate("/login", {
        replace: true,
        state: { returnTo: location.pathname + location.search },
      })
    }

    const onUnauthorized = () => goToLogin()
    const onStorage = (event) => {
      if (event.key === "token" && event.newValue === null) goToLogin()
    }

    window.addEventListener("auth:unauthorized", onUnauthorized)
    window.addEventListener("storage", onStorage)
    return () => {
      window.removeEventListener("auth:unauthorized", onUnauthorized)
      window.removeEventListener("storage", onStorage)
    }
  }, [navigate, location.pathname, location.search, queryClient])

  return null
}
