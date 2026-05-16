import { useState, useMemo } from "react"
import { useTranslation } from "react-i18next"
import { ChevronRight, FolderOpen } from "lucide-react"
import { casesApi } from "../../api/testcases"
import { useSuitesAll, sortSuitesHierarchically } from "../../hooks/useSuites"
import { TestCaseItem } from "./test-case-item"

function SuiteNode({ suite, casesBySuite, loadCases, selected, onToggle, excludeIds, depth }) {
  const { t } = useTranslation("suites")
  const allCases = casesBySuite[suite.id] ?? []
  const excluded = new Set(excludeIds)
  const visible = allCases.filter(tc => !excluded.has(tc.id))
  const allExcluded = allCases.length > 0 && visible.length === 0

  return (
    <div className={depth > 0 ? "border rounded-lg overflow-hidden" : ""}>
      <details className="group/suite" onToggle={() => loadCases(suite.id)}>
        <summary className={`flex items-center gap-2 cursor-pointer select-none list-none font-medium text-gray-800 dark:text-gray-100 bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${depth === 0 ? "px-3 py-2 text-sm" : "px-3 py-1.5 text-xs"}`}>
          <ChevronRight size={13} className="shrink-0 group-open/suite:rotate-90 transition-transform" />
          <FolderOpen size={13} className="text-yellow-500 shrink-0" />
          <span className="truncate flex-1">{suite.name}</span>
          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">({suite.test_case_ids?.length ?? 0})</span>
        </summary>
        <div className="px-2 py-1 space-y-0.5">
          {suite.children.length > 0 && (
            <div className="pl-4 mb-1 space-y-1.5 border-l-2 border-gray-100 dark:border-gray-800">
              {suite.children.map(child => (
                <SuiteNode key={child.id} suite={child} casesBySuite={casesBySuite} loadCases={loadCases}
                  selected={selected} onToggle={onToggle} excludeIds={excludeIds} depth={depth + 1} />
              ))}
            </div>
          )}
          {allExcluded && (
            <p className="text-xs text-gray-400 dark:text-gray-500 py-1 px-2">{t("picker.allExcluded")}</p>
          )}
          {visible.map(tc => (
            <label key={tc.id} className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors">
              <input
                type="checkbox"
                className="shrink-0"
                checked={selected.includes(tc.id)}
                onChange={() => onToggle(tc.id)}
              />
              <TestCaseItem tc={tc} />
            </label>
          ))}
        </div>
      </details>
    </div>
  )
}

export function CasePicker({ projectId, selected, onToggle, excludeIds = [], maxHeight = "max-h-64" }) {
  const { data: rawSuites = [] } = useSuitesAll(projectId)
  const [casesBySuite, setCasesBySuite] = useState({})

  const roots = useMemo(() => {
    const sorted = sortSuitesHierarchically(rawSuites)
    const map = Object.fromEntries(sorted.map(s => [s.id, { ...s, children: [] }]))
    const roots = []
    sorted.forEach(s => {
      if (s.parent_suite_id && map[s.parent_suite_id]) {
        map[s.parent_suite_id].children.push(map[s.id])
      } else {
        roots.push(map[s.id])
      }
    })
    return roots
  }, [rawSuites])

  const loadCases = async (suiteId) => {
    if (casesBySuite[suiteId]) return
    const cases = await casesApi.list(suiteId)
    setCasesBySuite(prev => ({ ...prev, [suiteId]: cases }))
  }

  return (
    <div className={`border rounded-lg ${maxHeight} overflow-y-auto divide-y`}>
      {roots.map(suite => (
        <SuiteNode key={suite.id} suite={suite} casesBySuite={casesBySuite} loadCases={loadCases}
          selected={selected} onToggle={onToggle} excludeIds={excludeIds} depth={0} />
      ))}
    </div>
  )
}
