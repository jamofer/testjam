import { useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"

/**
 * Listens for the `auth:unauthorized` event dispatched by the axios
 * interceptor on a 401 and soft-navigates to /login (preserving React state).
 * Saves the current path in router state so the login flow can return there.
 */
export function AuthRedirector() {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const handler = () => {
      if (location.pathname === "/login") return
      navigate("/login", {
        replace: true,
        state: { returnTo: location.pathname + location.search },
      })
    }
    window.addEventListener("auth:unauthorized", handler)
    return () => window.removeEventListener("auth:unauthorized", handler)
  }, [navigate, location.pathname, location.search])

  return null
}
