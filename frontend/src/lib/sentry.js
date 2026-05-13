import * as Sentry from '@sentry/react'

const SCRUB_BODY_KEYS = new Set([
  'password',
  'new_password',
  'current_password',
  'token',
  'access_token',
  'refresh_token',
  'api_key',
  'secret',
])

const SCRUB_HEADER_KEYS = new Set(['authorization', 'cookie', 'x-api-key'])

export function configureSentry() {
  const dsn = (import.meta.env.VITE_SENTRY_DSN || '').trim()
  if (!dsn) return

  Sentry.init({
    dsn,
    release: releaseTag(),
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE,
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0'),
    sendDefaultPii: false,
    beforeSend: scrubEvent,
    beforeSendTransaction: scrubEvent,
  })
}

export function scrubEvent(event) {
  const request = event?.request
  if (request) {
    request.headers = scrubMap(request.headers, SCRUB_HEADER_KEYS, (key) => key.toLowerCase())
    request.data = scrubMap(request.data, SCRUB_BODY_KEYS, (key) => key.toLowerCase())
    if (typeof request.query_string === 'string') {
      request.query_string = scrubQueryString(request.query_string)
    }
    if (typeof request.url === 'string') {
      request.url = scrubUrl(request.url)
    }
  }
  return event
}

function scrubQueryString(query) {
  const params = new URLSearchParams(query)
  let mutated = false
  for (const key of [...params.keys()]) {
    if (SCRUB_BODY_KEYS.has(key.toLowerCase())) {
      params.set(key, '[scrubbed]')
      mutated = true
    }
  }
  return mutated ? params.toString() : query
}

function scrubUrl(url) {
  const queryStart = url.indexOf('?')
  if (queryStart < 0) return url
  const base = url.slice(0, queryStart)
  const cleaned = scrubQueryString(url.slice(queryStart + 1))
  return `${base}?${cleaned}`
}

function releaseTag() {
  const explicit = (import.meta.env.VITE_APP_RELEASE || '').trim()
  if (explicit) return explicit
  const version = import.meta.env.VITE_APP_VERSION || '0.0.0'
  const sha = (import.meta.env.VITE_GIT_SHA || '').trim()
  return sha ? `testjam-frontend@${version}+${sha.slice(0, 12)}` : `testjam-frontend@${version}`
}

function scrubMap(source, sensitiveKeys, normalizeKey) {
  if (!source || typeof source !== 'object') return source
  const result = Array.isArray(source) ? [...source] : { ...source }
  for (const key of Object.keys(result)) {
    if (sensitiveKeys.has(normalizeKey(key))) {
      result[key] = '[scrubbed]'
    }
  }
  return result
}
