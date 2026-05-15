import { useMemo } from "react"
import { useMe } from "./useAuth"
import { browserTimezone } from "../lib/format"

export function useDatePreferences() {
  const { data: me } = useMe()
  return useMemo(() => ({
    timezone: me?.timezone || browserTimezone() || "UTC",
    useRelativeDates: me?.use_relative_dates ?? true,
  }), [me?.timezone, me?.use_relative_dates])
}
