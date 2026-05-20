import { useCallback, useEffect, useState } from "react"

const STORAGE_PREFIX = "testjam.cfColumns"

function storageKey(entityType, projectId) {
  return `${STORAGE_PREFIX}:${entityType}:${projectId}`
}

function readStored(entityType, projectId) {
  if (typeof window === "undefined" || !projectId) return []
  try {
    const raw = window.localStorage.getItem(storageKey(entityType, projectId))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function useCustomFieldColumns(entityType, projectId) {
  const [visibleKeys, setVisibleKeys] = useState(() => readStored(entityType, projectId))

  useEffect(() => {
    setVisibleKeys(readStored(entityType, projectId))
  }, [entityType, projectId])

  const persist = useCallback((next) => {
    if (typeof window === "undefined" || !projectId) return
    window.localStorage.setItem(storageKey(entityType, projectId), JSON.stringify(next))
  }, [entityType, projectId])

  const toggle = useCallback((key) => {
    setVisibleKeys(prev => {
      const next = prev.includes(key) ? prev.filter(item => item !== key) : [...prev, key]
      persist(next)
      return next
    })
  }, [persist])

  const clear = useCallback(() => {
    setVisibleKeys([])
    persist([])
  }, [persist])

  return { visibleKeys, toggle, clear }
}
