import { useMemo } from "react"
import { useTranslation } from "react-i18next"
import {
  CircleDot,
  FilePen,
  Link2,
  Link2Off,
  MessageSquare,
  MessageSquareDot,
  Paperclip,
  Sliders,
  User as UserIcon,
} from "lucide-react"

import { DateLabel } from "../ui/date-label"
import { MdViewer } from "../MdEditor"
import { lineDiff } from "../../lib/diff"

const STATUS_FIELD = "status"
const LINK_FIELD = "link"
const ATTACHMENT_FIELD = "attachment"
const COMMENT_FIELD = "comment"
const DESCRIPTION_FIELD = "description"
const CUSTOM_FIELD = "custom_field"

export function BugTimeline({ activity = [], comments = [], statuses, projectId }) {
  const { t } = useTranslation("bugs")

  const entries = useMemo(
    () => mergeEntries(activity, comments),
    [activity, comments],
  )

  if (entries.length === 0) {
    return <p className="text-sm text-gray-400 dark:text-gray-500">{t("history.empty")}</p>
  }

  return (
    <ul className="space-y-2">
      {entries.map(entry => (
        <li
          key={entry.key}
          className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-sm"
        >
          <header className="flex items-start justify-between gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-2">
              <EntryIcon entry={entry} />
              <UserIcon size={11} />
              <span>{entry.actor ?? "?"}</span>
              <span className="text-gray-700 dark:text-gray-200">
                {renderMessage(entry, t, statuses)}
              </span>
            </span>
            <DateLabel iso={entry.at} mode="relative" />
          </header>
          {entry.kind === "comment" && (
            <div className="mt-2">
              <MdViewer value={entry.body} projectId={projectId} />
            </div>
          )}
          {entry.kind === "activity" && entry.field === DESCRIPTION_FIELD && (
            <DescriptionDiff before={entry.fromValue} after={entry.toValue} />
          )}
          {entry.kind === "activity" && entry.note && entry.field !== CUSTOM_FIELD && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{entry.note}</p>
          )}
        </li>
      ))}
    </ul>
  )
}

function EntryIcon({ entry }) {
  if (entry.kind === "comment") {
    return <MessageSquare size={12} className="text-gray-400 dark:text-gray-500" />
  }
  if (entry.field === STATUS_FIELD) {
    return <CircleDot size={12} className="text-gray-400 dark:text-gray-500" />
  }
  if (entry.field === LINK_FIELD) {
    const Icon = entry.toValue ? Link2 : Link2Off
    return <Icon size={12} className="text-gray-400 dark:text-gray-500" />
  }
  if (entry.field === ATTACHMENT_FIELD) {
    return <Paperclip size={12} className="text-gray-400 dark:text-gray-500" />
  }
  if (entry.field === COMMENT_FIELD) {
    return <MessageSquareDot size={12} className="text-gray-400 dark:text-gray-500" />
  }
  if (entry.field === CUSTOM_FIELD) {
    return <Sliders size={12} className="text-gray-400 dark:text-gray-500" />
  }
  return <FilePen size={12} className="text-gray-400 dark:text-gray-500" />
}

function mergeEntries(activity, comments) {
  const activityEntries = activity.map(row => ({
    key: `a-${row.id}`,
    kind: "activity",
    at: row.changed_at,
    actor: row.changed_by?.username,
    field: row.field,
    fromValue: row.from_value,
    toValue: row.to_value,
    note: row.note,
  }))
  const commentEntries = comments.map(comment => ({
    key: `c-${comment.id}`,
    kind: "comment",
    at: comment.created_at,
    actor: comment.created_by?.username,
    body: comment.body,
  }))
  return [...activityEntries, ...commentEntries].sort(byTimestamp)
}

function byTimestamp(left, right) {
  if (left.at === right.at) return left.key.localeCompare(right.key)
  return left.at < right.at ? -1 : 1
}

function DescriptionDiff({ before, after }) {
  const rows = useMemo(() => lineDiff(before, after), [before, after])
  if (rows.length === 0) return null
  return (
    <pre className="mt-2 text-xs bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded p-2 whitespace-pre-wrap font-mono overflow-x-auto">
      {rows.map((row, index) => (
        <span key={index} className={diffLineClassName(row.type)}>
          {diffPrefix(row.type)}{row.text}{"\n"}
        </span>
      ))}
    </pre>
  )
}

function diffLineClassName(type) {
  if (type === "add") return "block text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/40"
  if (type === "del") return "block text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/40"
  return "block text-gray-500 dark:text-gray-500"
}

function diffPrefix(type) {
  if (type === "add") return "+ "
  if (type === "del") return "- "
  return "  "
}

function formatCustomFieldValue(raw) {
  if (raw == null) return null
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) return parsed.join(", ")
    return String(parsed)
  } catch {
    return raw
  }
}


function renderMessage(entry, t, statuses) {
  if (entry.kind === "comment") {
    return t("activity.commented")
  }
  if (entry.field === STATUS_FIELD) {
    const to = statuses[entry.toValue] ?? entry.toValue
    if (entry.fromValue == null) {
      return t("activity.statusInitial", { to })
    }
    const from = statuses[entry.fromValue] ?? entry.fromValue
    return t("activity.statusFrom", { from, to })
  }
  if (entry.field === LINK_FIELD) {
    return entry.toValue
      ? t("activity.linkAdded")
      : t("activity.linkRemoved")
  }
  if (entry.field === ATTACHMENT_FIELD) {
    return entry.toValue
      ? t("activity.attachmentAdded", { filename: entry.toValue })
      : t("activity.attachmentRemoved", { filename: entry.fromValue })
  }
  if (entry.field === COMMENT_FIELD) {
    return t("activity.commentUpdated")
  }
  if (entry.field === DESCRIPTION_FIELD) {
    if (entry.toValue == null) return t("activity.descriptionCleared")
    if (entry.fromValue == null) return t("activity.descriptionSet")
    return t("activity.descriptionEdited")
  }
  if (entry.field === CUSTOM_FIELD) {
    const key = entry.note ?? ""
    const from = formatCustomFieldValue(entry.fromValue)
    const to = formatCustomFieldValue(entry.toValue)
    if (to == null) return t("activity.customFieldCleared", { key })
    if (from == null) return t("activity.customFieldSet", { key, to })
    return t("activity.customFieldChanged", { key, from, to })
  }
  const field = t(`activity.fields.${entry.field}`, entry.field)
  if (entry.toValue == null) {
    return t("activity.cleared", { field })
  }
  if (entry.fromValue == null) {
    return t("activity.set", { field, to: entry.toValue })
  }
  return t("activity.changed", {
    field,
    from: entry.fromValue,
    to: entry.toValue,
  })
}
