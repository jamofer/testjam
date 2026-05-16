import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { Clock, ChevronRight } from "lucide-react"
import { useCaseRevisions, useCaseRevision } from "../../hooks/useSuites"
import { lineDiff } from "../../lib/diff"
import { DateLabel } from "../ui/date-label"
import { Skeleton, SkeletonList } from "../ui/skeleton"

function actorLabel(rev, fallback) {
  return rev.actor?.full_name || rev.actor?.username || fallback
}

function DiffLines({ before, after }) {
  const diff = useMemo(() => lineDiff(before, after), [before, after])
  const allEqual = diff.every(part => part.type === "eq")
  if (allEqual) return null
  return (
    <pre className="text-xs font-mono bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md overflow-x-auto">
      {diff.map((part, idx) => {
        const cls =
          part.type === "add" ? "bg-green-50 text-green-800" :
          part.type === "del" ? "bg-red-50 text-red-800 line-through opacity-80" :
          "text-gray-500 dark:text-gray-400"
        const sigil =
          part.type === "add" ? "+" :
          part.type === "del" ? "−" :
          " "
        return (
          <div key={idx} className={`px-2 py-0.5 ${cls}`}>
            <span className="select-none mr-2 text-gray-400 dark:text-gray-500">{sigil}</span>
            {part.text || " "}
          </div>
        )
      })}
    </pre>
  )
}

function StepsDiff({ before = [], after = [] }) {
  const beforeStr = before.map(step => `${step.order}. [${step.step_type}] ${step.action}${step.expected_result ? "  →  " + step.expected_result : ""}`).join("\n")
  const afterStr = after.map(step => `${step.order}. [${step.step_type}] ${step.action}${step.expected_result ? "  →  " + step.expected_result : ""}`).join("\n")
  return <DiffLines before={beforeStr} after={afterStr} />
}

function TagsDiff({ before = [], after = [] }) {
  const removed = before.filter(tag => !after.includes(tag))
  const added = after.filter(tag => !before.includes(tag))
  if (removed.length === 0 && added.length === 0) return null
  return (
    <div className="flex flex-wrap gap-1">
      {removed.map(tag => (
        <span key={"r-" + tag}
          className="text-[11px] px-1.5 py-0.5 rounded bg-red-50 text-red-700 line-through">{tag}</span>
      ))}
      {added.map(tag => (
        <span key={"a-" + tag}
          className="text-[11px] px-1.5 py-0.5 rounded bg-green-50 text-green-700">+{tag}</span>
      ))}
    </div>
  )
}

function ChangeSummary({ before, after }) {
  const { t } = useTranslation("cases")
  const TEXT_FIELDS = [
    ["name", t("history.fieldName")],
    ["description", t("history.fieldDescription")],
    ["preconditions", t("history.fieldPreconditions")],
    ["setup", t("history.fieldSetup")],
    ["teardown", t("history.fieldTeardown")],
    ["external_id", t("history.fieldExternalId")],
  ]
  if (!before) return <p className="text-xs text-gray-500 dark:text-gray-400">{t("history.initial")}</p>

  const changedSections = []
  for (const [key, label] of TEXT_FIELDS) {
    if ((before[key] ?? "") !== (after[key] ?? "")) {
      changedSections.push(
        <div key={key} className="space-y-1">
          <p className="text-[11px] uppercase tracking-wide font-semibold text-gray-500 dark:text-gray-400">{label}</p>
          <DiffLines before={before[key]} after={after[key]} />
        </div>
      )
    }
  }

  const tagsChanged = JSON.stringify(before.tags ?? []) !== JSON.stringify(after.tags ?? [])
  if (tagsChanged) {
    changedSections.push(
      <div key="tags" className="space-y-1">
        <p className="text-[11px] uppercase tracking-wide font-semibold text-gray-500 dark:text-gray-400">{t("history.fieldTags")}</p>
        <TagsDiff before={before.tags} after={after.tags} />
      </div>
    )
  }

  const stepsChanged = JSON.stringify(before.steps ?? []) !== JSON.stringify(after.steps ?? [])
  if (stepsChanged) {
    changedSections.push(
      <div key="steps" className="space-y-1">
        <p className="text-[11px] uppercase tracking-wide font-semibold text-gray-500 dark:text-gray-400">{t("history.fieldSteps")}</p>
        <StepsDiff before={before.steps} after={after.steps} />
      </div>
    )
  }

  if (changedSections.length === 0) {
    return <p className="text-xs text-gray-400 dark:text-gray-500">{t("history.noTextChanges")}</p>
  }
  return <div className="space-y-3">{changedSections}</div>
}

function RevisionRow({ rev, prevRev, expanded, onToggle, caseId }) {
  const { t } = useTranslation("cases")
  const { data: detail } = useCaseRevision(caseId, expanded ? rev.id : null)
  const { data: prevDetail } = useCaseRevision(caseId, expanded && prevRev ? prevRev.id : null)

  const kindBadge = rev.change_kind === "created"
    ? "bg-green-50 text-green-700 border-green-200"
    : "bg-blue-50 text-blue-700 border-blue-200"

  return (
    <li className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900">
      <button type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">
        <ChevronRight size={13}
          className={`text-gray-400 dark:text-gray-500 shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`} />
        <span className={`text-[10px] uppercase tracking-wide font-bold border px-1.5 py-0.5 rounded shrink-0 ${kindBadge}`}>
          {rev.change_kind}
        </span>
        <span className="text-sm text-gray-700 dark:text-gray-200 flex-1 truncate">{actorLabel(rev, t("history.actorSystem"))}</span>
        <span className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">
          <Clock size={11} /> <DateLabel iso={rev.created_at} />
        </span>
      </button>
      {expanded && (
        <div className="border-t border-gray-100 dark:border-gray-800 p-3 space-y-3">
          {!detail ? (
            <Skeleton className="h-12 w-full" />
          ) : (
            <ChangeSummary before={prevDetail?.snapshot} after={detail.snapshot} />
          )}
        </div>
      )}
    </li>
  )
}

export function CaseRevisions({ caseId }) {
  const { t } = useTranslation("cases")
  const { data: revs = [], isLoading } = useCaseRevisions(caseId)
  const [expandedId, setExpandedId] = useState(null)

  if (isLoading) return <SkeletonList count={3} itemClassName="h-10" />
  if (revs.length === 0) return <p className="text-sm text-gray-400 dark:text-gray-500">{t("history.empty")}</p>

  return (
    <ul className="space-y-2">
      {revs.map((rev, idx) => {
        const prevRev = revs[idx + 1]
        return (
          <RevisionRow key={rev.id} rev={rev} prevRev={prevRev} caseId={caseId}
            expanded={expandedId === rev.id}
            onToggle={() => setExpandedId(expandedId === rev.id ? null : rev.id)}
          />
        )
      })}
    </ul>
  )
}
