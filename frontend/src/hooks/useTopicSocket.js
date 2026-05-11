import { useEffect, useRef, useState } from 'react'

const BACKOFF_SCHEDULE_MS = [1000, 2000, 5000, 15000, 30000]
const HEARTBEAT_TIMEOUT_MS = 60000

export function useTopicSocket(topics, handlers, { enabled = true } = {}) {
  const topicsRef = useRef(topics)
  const handlersRef = useRef(handlers)
  const [connected, setConnected] = useState(false)

  useEffect(() => { topicsRef.current = topics }, [topics])
  useEffect(() => { handlersRef.current = handlers }, [handlers])

  useEffect(() => {
    if (!enabled) {
      setConnected(false)
      return undefined
    }
    const token = localStorage.getItem('token')
    if (!token) {
      setConnected(false)
      return undefined
    }

    let socket = null
    let cancelled = false
    let backoffAttempt = 0
    let reconnectTimer = null
    let heartbeatWatchdog = null

    const clearWatchdog = () => {
      if (heartbeatWatchdog) {
        clearTimeout(heartbeatWatchdog)
        heartbeatWatchdog = null
      }
    }

    const armWatchdog = () => {
      clearWatchdog()
      heartbeatWatchdog = setTimeout(() => closeSocket(socket), HEARTBEAT_TIMEOUT_MS)
    }

    const respondToPing = () => {
      try { socket.send(JSON.stringify({ action: 'pong' })) } catch { /* ignore */ }
      armWatchdog()
    }

    const connect = () => {
      if (cancelled) return
      socket = openSocket(token, {
        onOpen: () => {
          backoffAttempt = 0
          setConnected(true)
          armWatchdog()
          for (const topic of topicsRef.current) {
            socket.send(JSON.stringify({ action: 'subscribe', topic }))
          }
        },
        onMessage: (msg) => {
          if (msg?.event === 'ping') {
            respondToPing()
            return
          }
          dispatchEvent(msg, handlersRef.current)
        },
        onClose: () => {
          setConnected(false)
          clearWatchdog()
          if (cancelled) return
          reconnectTimer = setTimeout(connect, nextBackoff(backoffAttempt++))
        },
      })
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      clearWatchdog()
      setConnected(false)
      closeSocket(socket)
    }
  }, [enabled, serialiseTopics(topics)])

  return { connected }
}

function openSocket(token, { onOpen, onMessage, onClose }) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${proto}://${window.location.host}/api/v1/ws?token=${encodeURIComponent(token)}`
  const socket = new WebSocket(url)
  socket.onopen = onOpen
  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data))
    } catch {
      // ignore malformed frame
    }
  }
  socket.onerror = () => { /* let onclose drive the reconnect */ }
  socket.onclose = onClose
  return socket
}

function closeSocket(socket) {
  if (!socket) return
  if (socket.readyState === WebSocket.CONNECTING) {
    socket.addEventListener('open', () => socket.close(), { once: true })
    return
  }
  try { socket.close() } catch { /* already closed */ }
}

function dispatchEvent(msg, handlers) {
  if (!msg || typeof msg.event !== 'string') return
  const handler = handlers?.[msg.event]
  if (typeof handler === 'function') handler(msg.data, msg)
}

function nextBackoff(attempt) {
  return BACKOFF_SCHEDULE_MS[Math.min(attempt, BACKOFF_SCHEDULE_MS.length - 1)]
}

function serialiseTopics(topics) {
  return Array.isArray(topics) ? topics.join('|') : ''
}
