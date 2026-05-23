import i18n from "../i18n"

const SECONDS_PER_MINUTE = 60

export function loginErrorMessage(error) {
  const status = error?.response?.status
  const t = i18n.t.bind(i18n)
  if (status === 423) {
    const seconds = readRetryAfterSeconds(error)
    return t("auth:login.errors.locked", { window: formatRetryWindow(seconds, t) })
  }
  if (status === 429) {
    return t("auth:login.errors.tooMany")
  }
  return t("auth:login.errors.invalid")
}

function readRetryAfterSeconds(error) {
  const raw = error?.response?.headers?.["retry-after"]
  const parsed = parseInt(raw, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
}

function formatRetryWindow(seconds, t) {
  if (seconds <= 0) return t("auth:login.errors.retryMoments")
  if (seconds < SECONDS_PER_MINUTE) {
    return t("auth:login.errors.retrySeconds", { count: seconds })
  }
  const minutes = Math.ceil(seconds / SECONDS_PER_MINUTE)
  return t("auth:login.errors.retryMinutes", { count: minutes })
}
