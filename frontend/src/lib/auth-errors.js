const SECONDS_PER_MINUTE = 60

export function loginErrorMessage(error) {
  const status = error?.response?.status
  if (status === 423) {
    const seconds = readRetryAfterSeconds(error)
    return `Account locked due to too many failed login attempts. Try again in ${formatRetryWindow(seconds)}.`
  }
  if (status === 429) {
    return 'Too many login attempts. Please wait a minute before trying again.'
  }
  return 'Invalid credentials'
}

function readRetryAfterSeconds(error) {
  const raw = error?.response?.headers?.['retry-after']
  const parsed = parseInt(raw, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
}

function formatRetryWindow(seconds) {
  if (seconds <= 0) return 'a few moments'
  if (seconds < SECONDS_PER_MINUTE) {
    return `${seconds} second${seconds === 1 ? '' : 's'}`
  }
  const minutes = Math.ceil(seconds / SECONDS_PER_MINUTE)
  return `${minutes} minute${minutes === 1 ? '' : 's'}`
}
