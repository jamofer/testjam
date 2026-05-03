import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Upload, Tag, Clock } from 'lucide-react'
import { MdViewer } from '../components/MdEditor'
import { useExecution, useExecutionResults, useUpdateResult } from '../hooks/useExecutions'
import { executionsApi } from '../api/executions'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { toast } from 'sonner'

const STATUS_OPTIONS = ['passed', 'failed', 'blocked', 'not_run']

const statusColor = {
  passed:  'bg-green-100 text-green-700',
  failed:  'bg-red-100 text-red-600',
  blocked: 'bg-yellow-100 text-yellow-700',
  not_run: 'bg-gray-100 text-gray-500',
}

function ImportResultsButton({ executionId }) {
  const junitRef = useRef()
  const rfRef = useRef()
  const qc = useQueryClient()
  const [importing, setImporting] = useState(false)

  const handleImport = async (file, format) => {
    if (!file) return
    setImporting(true)
    try {
      const fn = format === 'junit'
        ? executionsApi.importJunit
        : executionsApi.importRobotFramework
      const result = await fn(executionId, file)
      qc.invalidateQueries({ queryKey: ['results', executionId] })
      qc.invalidateQueries({ queryKey: ['executions', executionId] })
      toast.success(`Imported: ${result.created} created, ${result.updated} updated${result.errors?.length ? `, ${result.errors.length} unmatched` : ''}`)
      if (result.errors?.length) {
        console.warn('Unmatched tests:', result.errors)
      }
    } catch (e) {
      toast.error(`Import failed: ${e.response?.data?.detail ?? e.message}`)
    } finally {
      setImporting(false)
      if (junitRef.current) junitRef.current.value = ''
      if (rfRef.current) rfRef.current.value = ''
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input ref={junitRef} type="file" accept=".xml" className="hidden"
        onChange={e => handleImport(e.target.files[0], 'junit')} />
      <input ref={rfRef} type="file" accept=".xml" className="hidden"
        onChange={e => handleImport(e.target.files[0], 'robotframework')} />
      <Button size="sm" variant="outline" disabled={importing}
        onClick={() => junitRef.current?.click()}>
        <Upload size={13} /> JUnit XML
      </Button>
      <Button size="sm" variant="outline" disabled={importing}
        onClick={() => rfRef.current?.click()}>
        <Upload size={13} /> Robot Framework
      </Button>
    </div>
  )
}

function fmtDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

export function ExecutionDetailPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const updateResult = useUpdateResult(id)

  if (!execution) return <p className="text-gray-500">Loading…</p>

  const versionLabel = execution.version ?? null

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{execution.title}</h1>
            <div className="flex items-center gap-2 mt-1 text-sm text-gray-500 flex-wrap">
              <span>{execution.type}</span>
              {versionLabel && (
                <span className="flex items-center gap-1 bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full text-xs font-medium">
                  <Tag size={10} /> {versionLabel}
                </span>
              )}
              {execution.environment && <span>· {execution.environment}</span>}
              {execution.triggered_by && <span>· by {execution.triggered_by}</span>}
            </div>
            {(execution.started_at || execution.finished_at) && (
              <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                {execution.started_at && (
                  <span className="flex items-center gap-1"><Clock size={10} /> {fmtDate(execution.started_at)}</span>
                )}
                {execution.finished_at && <span>→ {fmtDate(execution.finished_at)}</span>}
              </div>
            )}
          </div>
          {execution.type === 'automatic' && (
            <ImportResultsButton executionId={id} />
          )}
        </div>
        {execution.description && (
          <div className="mt-3">
            <MdViewer value={execution.description} />
          </div>
        )}
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex gap-4 text-sm">
          <span className="text-green-600 font-medium">✓ {execution.summary?.passed ?? 0} passed</span>
          <span className="text-red-500 font-medium">✗ {execution.summary?.failed ?? 0} failed</span>
          <span className="text-yellow-600 font-medium">⚠ {execution.summary?.blocked ?? 0} blocked</span>
          <span className="text-gray-400">— {execution.summary?.not_run ?? 0} not run</span>
        </div>
        {(execution.attachments ?? []).length > 0 && (
          <div className="flex gap-2 ml-auto">
            {execution.attachments.map(a => (
              <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600 border rounded px-2 py-1 bg-white hover:bg-gray-50 transition-colors">
                <Upload size={11} />{a.filename}
              </a>
            ))}
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
              <th className="text-left px-4 py-3 w-36">Completed at</th>
              <th className="text-left px-4 py-3 w-24">Duration</th>
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
                <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(result.executed_at) ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400 text-xs">
                  {result.duration_ms != null ? `${(result.duration_ms / 1000).toFixed(2)}s` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
