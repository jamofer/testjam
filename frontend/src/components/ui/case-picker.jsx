import { useEffect, useMemo, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { ChevronRight, FolderOpen } from "lucide-react"
import { casesApi } from "../../api/testcases"
import { useSuitesAll, sortSuitesHierarchically } from "../../hooks/useSuites"
import { TestCaseItem } from "./test-case-item"

export function CasePicker({ projectId, selected, onToggle, onToggleMany, excludeIds = [], maxHeight = "max-h-64" }) {
  const { data: rawSuites = [] } = useSuitesAll(projectId)
  const [casesBySuite, setCasesBySuite] = useState({})

  const roots = useMemo(() => {
    const sorted = sortSuitesHierarchically(rawSuites)
    const map = Object.fromEntries(sorted.map(s => [s.id, { ...s, children: [] }]))
    const topLevel = []
    sorted.forEach(s => {
      if (s.parent_suite_id && map[s.parent_suite_id]) {
        map[s.parent_suite_id].children.push(map[s.id])
      } else {
        topLevel.push(map[s.id])
      }
    })
    return topLevel
  }, [rawSuites])

  const loadCases = async (suiteId) => {
    if (casesBySuite[suiteId]) return
    const cases = await casesApi.list(suiteId)
    setCasesBySuite(previous => ({ ...previous, [suiteId]: cases }))
  }

  const toggleMany = onToggleMany ?? ((ids, shouldSelect) => {
    ids.forEach(id => {
      const alreadySelected = selected.includes(id)
      if (shouldSelect && !alreadySelected) onToggle(id)
      else if (!shouldSelect && alreadySelected) onToggle(id)
    })
  })

  return (
    <div className={`border rounded-lg ${maxHeight} overflow-y-auto divide-y`}>
      {roots.map(suite => (
        <SuiteNode key={suite.id} suite={suite} casesBySuite={casesBySuite} loadCases={loadCases}
          selected={selected} onToggle={onToggle} onToggleMany={toggleMany} excludeIds={excludeIds} depth={0} />
      ))}
    </div>
  )
}

function SuiteNode({ suite, casesBySuite, loadCases, selected, onToggle, onToggleMany, excludeIds, depth }) {
  const { t } = useTranslation("suites")
  const allCases = casesBySuite[suite.id] ?? []
  const excluded = new Set(excludeIds)
  const visible = allCases.filter(testCase => !excluded.has(testCase.id))
  const allExcluded = allCases.length > 0 && visible.length === 0

  const subtreeCaseIds = useMemo(() => collectSubtreeCaseIds(suite, excluded), [suite, excludeIds])
  const selectedSet = useMemo(() => new Set(selected), [selected])
  const selectedSubtreeCount = subtreeCaseIds.filter(id => selectedSet.has(id)).length
  const allSelected = subtreeCaseIds.length > 0 && selectedSubtreeCount === subtreeCaseIds.length
  const someSelected = selectedSubtreeCount > 0 && !allSelected

  const checkboxRef = useRef(null)
  useEffect(() => {
    if (checkboxRef.current) checkboxRef.current.indeterminate = someSelected
  }, [someSelected])

  const toggleAll = (event) => {
    event.stopPropagation()
    event.preventDefault()
    if (subtreeCaseIds.length === 0) return
    onToggleMany(subtreeCaseIds, !allSelected)
  }

  return (
    <div className={depth > 0 ? "border rounded-lg overflow-hidden" : ""}>
      <details className="group/suite" onToggle={() => loadCases(suite.id)}>
        <summary className={`flex items-center gap-2 cursor-pointer select-none list-none font-medium text-gray-800 dark:text-gray-100 bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${depth === 0 ? "px-3 py-2 text-sm" : "px-3 py-1.5 text-xs"}`}>
          <ChevronRight size={13} className="shrink-0 group-open/suite:rotate-90 transition-transform" />
          <input
            ref={checkboxRef}
            type="checkbox"
            className="shrink-0"
            checked={allSelected}
            disabled={subtreeCaseIds.length === 0}
            onChange={toggleAll}
            onClick={(event) => event.stopPropagation()}
            aria-label={t("picker.selectAllInSuite", { name: suite.name })}
          />
          <FolderOpen size={13} className="text-yellow-500 shrink-0" />
          <span className="truncate flex-1">{suite.name}</span>
          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">({suite.test_case_ids?.length ?? 0})</span>
        </summary>
        <div className="px-2 py-1 space-y-0.5">
          {suite.children.length > 0 && (
            <div className="pl-4 mb-1 space-y-1.5 border-l-2 border-gray-100 dark:border-gray-800">
              {suite.children.map(child => (
                <SuiteNode key={child.id} suite={child} casesBySuite={casesBySuite} loadCases={loadCases}
                  selected={selected} onToggle={onToggle} onToggleMany={onToggleMany} excludeIds={excludeIds} depth={depth + 1} />
              ))}
            </div>
          )}
          {allExcluded && (
            <p className="text-xs text-gray-400 dark:text-gray-500 py-1 px-2">{t("picker.allExcluded")}</p>
          )}
          {visible.map(testCase => (
            <label key={testCase.id} className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors">
              <input
                type="checkbox"
                className="shrink-0"
                checked={selected.includes(testCase.id)}
                onChange={() => onToggle(testCase.id)}
              />
              <TestCaseItem tc={testCase} />
            </label>
          ))}
        </div>
      </details>
    </div>
  )
}

function collectSubtreeCaseIds(suite, excluded) {
  const out = []
  for (const id of suite.test_case_ids ?? []) {
    if (!excluded.has(id)) out.push(id)
  }
  for (const child of suite.children ?? []) {
    out.push(...collectSubtreeCaseIds(child, excluded))
  }
  return out
}
