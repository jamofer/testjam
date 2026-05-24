// Coerce admin-typed "default value" strings from the custom-field
// dialog into the typed payload the API expects. Lives apart from
// `CustomFieldsPanel.jsx` so the rules are unit-testable and a single
// fix covers every entry point.

const TRUE_STRINGS = new Set(["true", "1", "yes", "y", "on", "sí", "si", "s"])
const FALSE_STRINGS = new Set(["false", "0", "no", "n", "off"])
const MULTI_SELECT_SEPARATOR = "|"


export function coerceDefault(type, raw) {
  if (type === "number") return Number(raw)
  if (type === "bool") return coerceBool(raw)
  if (type === "multi_select") {
    return String(raw)
      .split(MULTI_SELECT_SEPARATOR)
      .map(item => item.trim())
      .filter(Boolean)
  }
  return raw
}


function coerceBool(raw) {
  const normalized = String(raw).toLowerCase().trim()
  if (FALSE_STRINGS.has(normalized)) return false
  return TRUE_STRINGS.has(normalized)
}
