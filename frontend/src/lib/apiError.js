import { toast } from "sonner"

const toastIds = new WeakMap()
let nextToastId = 0

/**
 * Readable text for a failed API call. FastAPI sends `detail` as a string,
 * a list of validation errors or an object with a `message`; anything else
 * falls back to the caller's text.
 */
export function apiErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail
  if (typeof detail === "string" && detail) return detail
  if (Array.isArray(detail)) {
    const messages = detail.map(item => item?.msg).filter(Boolean)
    if (messages.length) return messages.join("; ")
  }
  if (typeof detail?.message === "string" && detail.message) return detail.message
  return fallback
}

/**
 * Show one toast per failed request. The global mutation handler and the
 * component that triggered the mutation both report the same error; sharing
 * the toast id lets the component's more specific text replace the generic
 * one instead of stacking two toasts.
 */
export function toastApiError(error, fallback, format = message => message) {
  toast.error(format(apiErrorMessage(error, fallback)), { id: toastIdFor(error) })
}

function toastIdFor(error) {
  if (error === null || typeof error !== "object") return undefined
  if (!toastIds.has(error)) toastIds.set(error, `api-error-${++nextToastId}`)
  return toastIds.get(error)
}
