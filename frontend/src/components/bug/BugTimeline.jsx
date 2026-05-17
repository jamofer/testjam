import { useMemo } from "react"
import { useTranslation } from "react-i18next"
import {
  CircleDot,
  FilePen,
  Link2,
  Link2Off,
  MessageSquare,
  User as UserIcon,
} from "lucide-react"

import { DateLabel } from "../ui/date-label"
import { MdViewer } from "../MdEditor"

const STATUS_FIELD = "status"
const LINK_FIELD = "link"

export function BugTimeline({ activity = [], comments = [], statuses }) {
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
              <MdViewer value={entry.body} />
            </div>
          )}
          {entry.kind === "activity" && entry.note && (
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
