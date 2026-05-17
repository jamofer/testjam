import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { createPortal } from "react-dom"
import {
  autoUpdate,
  flip,
  offset,
  shift,
  useFloating,
} from "@floating-ui/react"
import { useTranslation } from "react-i18next"

import { caretViewportRect } from "../../lib/mentions/caretCoords"
import {
  buildCanonicalToken,
  detectActiveTrigger,
  replaceRange,
} from "../../lib/mentions/triggerDetection"
import { useMentionSearch, useSelectedIndex } from "../../hooks/useMentionSearch"

// Watches a textarea for trigger characters (@ # ! ~) and renders a floating
// popover with autocomplete hits. On selection it rewrites the textarea value
// in place and calls `onChange` so the surrounding MdEditor stays in sync.
export function MentionAutocomplete({ textarea, value, onChange, projectId }) {
  const { t } = useTranslation("bugs")
  const [active, setActive] = useState(null)
  const close = useCallback(() => setActive(null), [])

  const { data: hits = [], isFetching } = useMentionSearch(
    projectId,
    active?.kind,
    active?.query ?? "",
    { enabled: !!active, parents: active?.parents ?? [] },
  )
  const [selectedIndex, setSelectedIndex] = useSelectedIndex(hits)

  const virtualReference = useMemo(() => buildVirtualReference(active?.rect), [active?.rect])
  const { refs, floatingStyles } = useFloating({
    placement: "bottom-start",
    middleware: [offset(6), flip(), shift({ padding: 8 })],
    whileElementsMounted: autoUpdate,
    open: !!active,
  })

  useEffect(() => {
    if (virtualReference) refs.setReference(virtualReference)
  }, [virtualReference, refs])

  const refreshActive = useCallback(() => {
    if (!textarea) return
    const caret = textarea.selectionStart ?? 0
    const next = detectActiveTrigger(textarea.value, caret)
    if (!next) {
      setActive(null)
      return
    }
    const rect = caretViewportRect(textarea, next.anchorIndex)
    setActive({ ...next, rect })
  }, [textarea])

  useEffect(() => {
    if (!textarea) return undefined
    const handle = () => refreshActive()
    textarea.addEventListener("keyup", handle)
    textarea.addEventListener("click", handle)
    textarea.addEventListener("blur", close)
    return () => {
      textarea.removeEventListener("keyup", handle)
      textarea.removeEventListener("click", handle)
      textarea.removeEventListener("blur", close)
    }
  }, [textarea, refreshActive, close])

  const insertHit = useCallback((hit) => {
    if (!active) return
    const token = buildCanonicalToken(active.triggerChar, hit)
    const nextValue = replaceRange(value ?? "", active.anchorIndex, active.caretIndex, token)
    onChange?.(nextValue)
    setActive(null)
    requestAnimationFrame(() => {
      if (!textarea) return
      const cursor = active.anchorIndex + token.length
      textarea.focus()
      textarea.setSelectionRange(cursor, cursor)
    })
  }, [active, value, onChange, textarea])

  useEffect(() => {
    if (!textarea || !active) return undefined
    const onKeyDown = (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault()
        setSelectedIndex(index => Math.min(index + 1, hits.length - 1))
      } else if (event.key === "ArrowUp") {
        event.preventDefault()
        setSelectedIndex(index => Math.max(index - 1, 0))
      } else if (event.key === "Enter" || event.key === "Tab") {
        if (hits[selectedIndex]) {
          event.preventDefault()
          insertHit(hits[selectedIndex])
        }
      } else if (event.key === "Escape") {
        event.preventDefault()
        close()
      }
    }
    textarea.addEventListener("keydown", onKeyDown)
    return () => textarea.removeEventListener("keydown", onKeyDown)
  }, [textarea, active, hits, selectedIndex, insertHit, setSelectedIndex, close])

  if (!active) return null
  const popover = (
    <div
      ref={refs.setFloating}
      style={floatingStyles}
      className="z-50 min-w-[280px] max-w-[420px] rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg overflow-hidden"
    >
      {hits.length === 0 ? (
        <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400">
          {isFetching ? t("mentions.searching") : t("mentions.noMatches")}
        </div>
      ) : (
        <ul className="max-h-64 overflow-auto py-1">
          {hits.map((hit, index) => (
            <li
              key={`${hit.kind}-${hit.id ?? hit.slug}`}
              className={`px-3 py-1.5 text-sm cursor-pointer ${
                index === selectedIndex
                  ? "bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300"
                  : "text-gray-800 dark:text-gray-100"
              }`}
              onMouseDown={(event) => { event.preventDefault(); insertHit(hit) }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="font-medium truncate">{hit.label}</div>
              {hit.description && (
                <div className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
                  {hit.description}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
  return createPortal(popover, document.body)
}

function buildVirtualReference(rect) {
  if (!rect) return null
  return {
    getBoundingClientRect: () => rect,
  }
}
