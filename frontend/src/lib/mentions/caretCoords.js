// Computes the pixel coordinates of the caret inside a textarea by mirroring
// it in an off-screen <div>. Returns viewport-relative coordinates so a
// floating popover can be anchored directly at the caret.
//
// Standard textarea-caret-position trick: clone the textarea styles into a
// div, render the text up to the caret followed by a marker <span>, then read
// the marker's bounding rect.

const MIRRORED_STYLES = [
  "boxSizing", "width", "height",
  "overflowX", "overflowY",
  "borderTopWidth", "borderRightWidth", "borderBottomWidth", "borderLeftWidth",
  "borderStyle",
  "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
  "fontStyle", "fontVariant", "fontWeight", "fontStretch", "fontSize", "fontSizeAdjust",
  "lineHeight", "fontFamily",
  "textAlign", "textTransform", "textIndent", "textDecoration",
  "letterSpacing", "wordSpacing",
  "tabSize", "MozTabSize",
]

export function caretViewportRect(textarea, caretIndex) {
  if (!textarea) return null
  const mirror = document.createElement("div")
  const style = mirror.style
  style.whiteSpace = "pre-wrap"
  style.wordWrap = "break-word"
  style.position = "absolute"
  style.visibility = "hidden"
  style.top = "0"
  style.left = "-9999px"

  const computed = window.getComputedStyle(textarea)
  for (const property of MIRRORED_STYLES) {
    style[property] = computed[property]
  }

  mirror.textContent = textarea.value.substring(0, caretIndex)
  const marker = document.createElement("span")
  marker.textContent = textarea.value.substring(caretIndex) || "."
  mirror.appendChild(marker)

  document.body.appendChild(mirror)
  const textareaRect = textarea.getBoundingClientRect()
  const markerRect = marker.getBoundingClientRect()
  const mirrorRect = mirror.getBoundingClientRect()

  const x = textareaRect.left + (markerRect.left - mirrorRect.left) - textarea.scrollLeft
  const y = textareaRect.top + (markerRect.top - mirrorRect.top) - textarea.scrollTop
  const height = markerRect.height

  document.body.removeChild(mirror)
  return { x, y, width: 1, height, top: y, left: x, right: x + 1, bottom: y + height }
}
