import { lazy, Suspense, useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { useTheme } from "../hooks/useTheme"
import { api } from "../api/client"
import { downloadBlob } from "../lib/download"
import {
  MentionChip,
  chipPropsFromAttributes,
  isMentionElement,
} from "./mention/MentionChip"
import { MentionAutocomplete } from "./mention/MentionAutocomplete"
import { MentionResolveProvider } from "./mention/MentionResolveContext"
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
  const markdown = (
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
  if (!projectId) return markdown
  return (
    <MentionResolveProvider projectId={projectId} source={value}>
      {markdown}
    </MentionResolveProvider>
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
    a: ({ node, children, href, ...props }) => (
      <AuthenticatedLink href={href} {...props}>{children}</AuthenticatedLink>
    ),
    img: ({ node, src, alt, ...props }) => (
      <AuthenticatedImage src={src} alt={alt} {...props} />
    ),
  }
}

const API_ATTACHMENT_PATTERN = /^\/api\/v1\/(?:bugs|cases|results|executions)\/\d+\/attachments\/\d+\/download(?:\?.*)?$/

function isAuthedAttachmentHref(href) {
  if (!href) return false
  try {
    const parsed = new URL(href, window.location.origin)
    if (parsed.origin !== window.location.origin) return false
    return API_ATTACHMENT_PATTERN.test(parsed.pathname + parsed.search)
  } catch {
    return false
  }
}

function AuthenticatedLink({ href, children, ...props }) {
  const handleClick = async (event) => {
    if (!isAuthedAttachmentHref(href)) return
    event.preventDefault()
    try {
      const parsed = new URL(href, window.location.origin)
      const response = await api.get(parsed.pathname + parsed.search, { responseType: "blob" })
      const fallback = parsed.pathname.split("/").pop() || "download"
      downloadBlob(response.data, fallback)
    } catch {
      toast.error("Download failed")
    }
  }
  return <a href={href} {...props} onClick={handleClick}>{children}</a>
}

function AuthenticatedImage({ src, alt, ...props }) {
  const [objectUrl, setObjectUrl] = useState(null)
  const needsAuth = isAuthedAttachmentHref(src)

  useEffect(() => {
    if (!needsAuth) return undefined
    let cancelled = false
    let createdUrl = null
    const parsed = new URL(src, window.location.origin)
    api
      .get(parsed.pathname + parsed.search, { responseType: "blob" })
      .then(response => {
        if (cancelled) return
        createdUrl = URL.createObjectURL(response.data)
        setObjectUrl(createdUrl)
      })
      .catch(() => {})
    return () => {
      cancelled = true
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
  }, [src, needsAuth])

  if (!needsAuth) return <img src={src} alt={alt} {...props} />
  if (!objectUrl) return <span className="text-xs text-gray-400">{alt ?? src}</span>
  return <img src={objectUrl} alt={alt} {...props} />
}

function sanitizeSpanProps(props) {
  const out = {}
  for (const [key, value] of Object.entries(props)) {
    if (!key.startsWith("data-mention")) out[key] = value
  }
  return out
}
