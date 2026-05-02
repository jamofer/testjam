import { useParams } from 'react-router-dom'
import { MdViewer } from '../components/MdEditor'
import { useExecution, useExecutionResults, useUpdateResult } from '../hooks/useExecutions'

const STATUS_OPTIONS = ['passed', 'failed', 'blocked', 'not_run']

const statusColor = {
  passed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-600',
  blocked: 'bg-yellow-100 text-yellow-700',
  not_run: 'bg-gray-100 text-gray-500',
}

export function ExecutionDetailPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const updateResult = useUpdateResult(id)

  if (!execution) return <p className="text-gray-500">Loading…</p>

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">{execution.title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {execution.type} · v{execution.version} · {execution.environment}
        </p>
        {execution.description && (
          <div className="mt-3">
            <MdViewer value={execution.description} />
          </div>
        )}
      </div>

      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3">Test Case</th>
              <th className="text-left px-4 py-3 w-36">Status</th>
              <th className="text-left px-4 py-3">Executed by</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.map(result => (
              <tr key={result.id}>
                <td className="px-4 py-3 font-medium text-gray-800">{result.test_case_title}</td>
                <td className="px-4 py-3">
                  <select
                    value={result.status}
                    onChange={e => updateResult.mutate({ id: result.id, data: { status: e.target.value } })}
                    className={`text-xs rounded-full px-2 py-1 font-medium border-0 cursor-pointer ${statusColor[result.status]}`}
                  >
                    {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </td>
                <td className="px-4 py-3 text-gray-500">{result.executed_by ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
