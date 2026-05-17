import { lazy, Suspense, useEffect, useRef, useState } from "react"
import { useTheme } from "../hooks/useTheme"
import {
  MentionChip,
  chipPropsFromAttributes,
  isMentionElement,
} from "./mention/MentionChip"
import { MentionAutocomplete } from "./mention/MentionAutocomplete"
import { rehypeMentions } from "../lib/mentions/rehypeMentions"

// `@uiw/react-md-editor` ships ~400 KB (Monaco-like editor + markdown deps).
// Lazy-load so it stays out of the initial bundle and only ships when a page
// actually mounts <MdEditor> or <MdViewer>.
const MDEditor = lazy(() => import("@uiw/react-md-editor"))
const MDEditorMarkdown = lazy(() =>
  import("@uiw/react-md-editor").then(m => ({ default: m.default.Markdown }))
)

const VIEWER_REHYPE_PLUGINS = [rehypeMentions]

export function MdEditor({ value, onChange, height = 200, projectId }) {
  const { appearance } = useTheme()
  const containerRef = useRef(null)
  const textarea = useTextareaFrom(containerRef)
  return (
    <div data-color-mode={appearance} ref={containerRef}>
      <Suspense fallback={<div style={{ height }} className="bg-gray-50 dark:bg-gray-900 animate-pulse rounded border" />}>
        <MDEditor value={value} onChange={onChange} height={height} preview="edit" />
      </Suspense>
      {projectId && textarea && (
        <MentionAutocomplete
          textarea={textarea}
          value={value}
          onChange={onChange}
          projectId={projectId}
        />
      )}
    </div>
  )
}

// `@uiw/react-md-editor` does not forward refs to its internal <textarea>, so
// we discover it through the container with a MutationObserver — the editor
// mounts lazily and may swap nodes during edits.
function useTextareaFrom(containerRef) {
  const [textarea, setTextarea] = useState(null)
  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined
    const sync = () => {
      const found = container.querySelector("textarea")
      setTextarea(current => (current === found ? current : found))
    }
    sync()
    const observer = new MutationObserver(sync)
    observer.observe(container, { childList: true, subtree: true })
    return () => observer.disconnect()
  }, [containerRef])
  return textarea
}

export function MdViewer({ value, projectId }) {
  const { appearance } = useTheme()
  if (!value) return null
  const components = buildViewerComponents(projectId)
  return (
    <div data-color-mode={appearance} className="md">
      <Suspense fallback={null}>
        <MDEditorMarkdown
          source={value}
          rehypePlugins={VIEWER_REHYPE_PLUGINS}
          components={components}
        />
      </Suspense>
    </div>
  )
}

function buildViewerComponents(projectId) {
  return {
    span: ({ node, children, ...props }) => {
      if (!isMentionElement(props)) {
        return <span {...sanitizeSpanProps(props)}>{children}</span>
      }
      return <MentionChip projectId={projectId} {...chipPropsFromAttributes(props)} />
    },
  }
}

function sanitizeSpanProps(props) {
  const out = {}
  for (const [key, value] of Object.entries(props)) {
    if (!key.startsWith("data-mention")) out[key] = value
  }
  return out
}
