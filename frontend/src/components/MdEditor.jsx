import { lazy, Suspense } from "react"
import { useTheme } from "../hooks/useTheme"

// `@uiw/react-md-editor` ships ~400 KB (Monaco-like editor + markdown deps).
// Lazy-load so it stays out of the initial bundle and only ships when a page
// actually mounts <MdEditor> or <MdViewer>.
const MDEditor = lazy(() => import("@uiw/react-md-editor"))
const MDEditorMarkdown = lazy(() =>
  import("@uiw/react-md-editor").then(m => ({ default: m.default.Markdown }))
)

export function MdEditor({ value, onChange, height = 200 }) {
  const { appearance } = useTheme()
  return (
    <div data-color-mode={appearance}>
      <Suspense fallback={<div style={{ height }} className="bg-gray-50 dark:bg-gray-900 animate-pulse rounded border" />}>
        <MDEditor value={value} onChange={onChange} height={height} preview="edit" />
      </Suspense>
    </div>
  )
}

export function MdViewer({ value }) {
  const { appearance } = useTheme()
  if (!value) return null
  return (
    <div data-color-mode={appearance} className="md">
      <Suspense fallback={null}>
        <MDEditorMarkdown source={value} />
      </Suspense>
    </div>
  )
}
