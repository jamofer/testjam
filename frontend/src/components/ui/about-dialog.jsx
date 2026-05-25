import { useTranslation } from "react-i18next"
import { Github } from "lucide-react"
import { Dialog, DialogContent, DialogTitle } from "./dialog"
import { Logo } from "./logo"
import { useAbout } from "../../hooks/useAbout"
import { useDatePreferences } from "../../hooks/useDatePreferences"
import { fmtDate } from "../../lib/format"

const REPO_URL = "https://github.com/jamofer/testjam"

export function AboutDialog({ open, onOpenChange }) {
  const { t } = useTranslation("about")
  const { data, isLoading } = useAbout()
  const { timezone } = useDatePreferences()

  const displayRef = formatRef(data)
  const builtAt = data?.built_at && data.built_at !== "unknown"
    ? fmtDate(data.built_at, timezone)
    : t("unknown")

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle className="sr-only">Testjam</DialogTitle>
        <div className="mb-4">
          <Logo size={28} />
        </div>

        {isLoading ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("loading")}</p>
        ) : (
          <dl className="space-y-2 text-sm">
            <Row label={t("fields.release")} value={displayRef} mono />
            <Row label={t("fields.commit")} value={data?.commit ?? t("unknown")} mono />
            <Row label={t("fields.builtAt")} value={builtAt} />
          </dl>
        )}

        <div className="mt-5 pt-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{t("license")}</span>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 hover:text-gray-800 dark:hover:text-gray-200"
          >
            <Github size={12} /> {t("source")}
          </a>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function aboutShortLabel(data) {
  if (!data) return null
  const ref = data.ref && data.ref !== "unknown" ? data.ref : null
  const commit = data.commit && data.commit !== "unknown" ? data.commit : null
  if (isReleaseTag(ref)) return ref
  if (ref && commit) return `${ref} @ ${commit}`
  if (ref) return ref
  if (commit) return commit
  return `v${data.version}`
}

function formatRef(data) {
  if (!data) return ""
  if (isReleaseTag(data.ref)) return data.ref
  const ref = data.ref && data.ref !== "unknown" ? data.ref : null
  const commit = data.commit && data.commit !== "unknown" ? data.commit : null
  if (ref && commit) return `${ref} @ ${commit}`
  return ref || commit || `v${data.version}`
}

function isReleaseTag(ref) {
  return typeof ref === "string" && /^v\d/.test(ref)
}

function Row({ label, value, mono = false }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="text-gray-500 dark:text-gray-400">{label}</dt>
      <dd className={`text-gray-800 dark:text-gray-200 text-right ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </dd>
    </div>
  )
}
