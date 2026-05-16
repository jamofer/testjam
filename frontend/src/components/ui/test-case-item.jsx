import { FileText } from "lucide-react"

export function buildSuitePath(suiteId, suites) {
  const map = Object.fromEntries((suites ?? []).map(s => [s.id, s]))
  const path = []
  let id = suiteId
  while (id && map[id]) {
    path.unshift(map[id].name)
    id = map[id].parent_suite_id
  }
  return path.join(" › ")
}

export function mapSuiteByCase(suites) {
  const map = {}
  ;(suites ?? []).forEach(suite => {
    (suite.test_case_ids ?? []).forEach(caseId => { map[caseId] = suite })
  })
  return map
}

export function TestCaseItem({ tc, suites }) {
  const path = suites ? buildSuitePath(tc.suite_id, suites) : null
  return (
    <div className="flex items-start gap-2 min-w-0">
      <FileText size={13} className="text-gray-400 dark:text-gray-500 shrink-0 mt-px" />
      <div className="min-w-0">
        {path && (
          <p className="text-[11px] leading-none text-gray-400 dark:text-gray-500 truncate mb-0.5">{path}</p>
        )}
        <p className="text-sm text-gray-800 dark:text-gray-100 leading-snug truncate">{tc.name}</p>
      </div>
    </div>
  )
}
