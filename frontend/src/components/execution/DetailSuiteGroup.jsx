import { Link } from "react-router-dom"
import { ChevronRight, FolderOpen } from "lucide-react"
import { STATUS_KEYS, STATUS_CONFIG } from "../../lib/statusConfig"

function fmtDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

export const TABLE_HEAD = (
  <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
    <tr>
      <th className="text-left px-4 py-3">Test Case</th>
      <th className="text-left px-4 py-3 w-36">Status</th>
      <th className="text-left px-4 py-3">Executed by</th>
      <th className="text-left px-4 py-3 w-36">Completed at</th>
      <th className="text-left px-4 py-3 w-24">Duration</th>
    </tr>
  </thead>
)

export function ResultRows({ items, updateResult }) {
  return items.map(result => (
    <tr key={result.id}>
      <td className="px-4 py-3">
        <Link to={`/cases/${result.test_case_id}`} className="font-medium text-gray-800 hover:text-blue-600 hover:underline">
          {result.test_case_title ?? "—"}
        </Link>
      </td>
      <td className="px-4 py-3">
        <select
          value={result.status}
          onChange={e => updateResult.mutate({ id: result.id, data: { status: e.target.value } })}
          className={`text-xs rounded-full px-2 py-1 font-medium border-0 cursor-pointer ${STATUS_CONFIG[result.status]?.pill ?? ""}`}
        >
          {STATUS_KEYS.map(s => <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>)}
        </select>
      </td>
      <td className="px-4 py-3 text-gray-500">{result.executed_by ?? "—"}</td>
      <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(result.executed_at) ?? "—"}</td>
      <td className="px-4 py-3 text-gray-400 text-xs">
        {result.duration_ms != null ? `${(result.duration_ms / 1000).toFixed(2)}s` : "—"}
      </td>
    </tr>
  ))
}

export function DetailSuiteGroup({ suiteId, groups, childrenOf, updateResult }) {
  const { suite, items } = groups[suiteId]
  const children = childrenOf[suiteId] ?? []

  return (
    <div className="border rounded-lg overflow-hidden">
      <details open className="group/suite">
        <summary className="flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer list-none font-medium text-sm text-gray-800">
          <ChevronRight size={14} className="transition-transform shrink-0 group-open/suite:rotate-90" />
          <FolderOpen size={14} className="text-yellow-500 shrink-0" />
          <span className="truncate flex-1">{suite.name}</span>
          <span className="text-xs text-gray-400 shrink-0">({items.length})</span>
        </summary>
        {items.length > 0 && (
          <table className="w-full text-sm">
            {TABLE_HEAD}
            <tbody className="divide-y divide-gray-100">
              <ResultRows items={items} updateResult={updateResult} />
            </tbody>
          </table>
        )}
        {children.length > 0 && (
          <div className="px-3 pb-3 pt-2 pl-6 space-y-2 border-l-2 border-gray-100 ml-3">
            {children.map(childId => (
              <DetailSuiteGroup key={childId} suiteId={childId} groups={groups} childrenOf={childrenOf} updateResult={updateResult} />
            ))}
          </div>
        )}
      </details>
    </div>
  )
}
