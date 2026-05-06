import { useRef, useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Upload, Tag, Clock, Download, FolderOpen, ChevronRight } from 'lucide-react'
import { MdViewer } from '../components/MdEditor'
import { useExecution, useExecutionResults, useUpdateResult } from '../hooks/useExecutions'
import { executionsApi } from '../api/executions'
import { useProject } from '../hooks/useProjects'
import { useSuitesAll, sortSuitesHierarchically } from '../hooks/useSuites'
import { mapSuiteByCase, buildSuitePath } from '../components/ui/test-case-item'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { Skeleton, SkeletonList } from '../components/ui/skeleton'
import { STATUS_KEYS, STATUS_CONFIG } from '../lib/statusConfig'
import { toast } from 'sonner'

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

async function downloadPdf(execution, results, projectName) {
  const { exportExecutionPdf } = await import('../lib/exportPdf')
  exportExecutionPdf(execution, results, projectName)
}

function fmtDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

function ResultRows({ items, updateResult }) {
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
      <td className="px-4 py-3 text-gray-500">{result.executed_by ?? '—'}</td>
      <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(result.executed_at) ?? '—'}</td>
      <td className="px-4 py-3 text-gray-400 text-xs">
        {result.duration_ms != null ? `${(result.duration_ms / 1000).toFixed(2)}s` : '—'}
      </td>
    </tr>
  ))
}

const TABLE_HEAD = (
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

function buildDetailTree(groups, allSuites) {
  const order = sortSuitesHierarchically(allSuites).map(s => s.id)
  const suiteMap = Object.fromEntries(allSuites.map(s => [s.id, s]))

  const full = { ...groups }
  Object.values(groups).forEach(({ suite }) => {
    if (!suite) return
    let pid = suite.parent_suite_id
    while (pid && !full[pid]) {
      const ancestor = suiteMap[pid]
      if (!ancestor) break
      full[pid] = { suite: ancestor, items: [] }
      pid = ancestor.parent_suite_id
    }
  })

  const topLevelIds = []
  const childrenOf = {}

  Object.values(full).forEach(({ suite }) => {
    if (!suite) return
    const parentId = suite.parent_suite_id
    if (parentId && full[parentId]) {
      if (!childrenOf[parentId]) childrenOf[parentId] = []
      childrenOf[parentId].push(suite.id)
    } else {
      topLevelIds.push(suite.id)
    }
  })

  const sort = (ids) => ids.sort((a, b) => order.indexOf(a) - order.indexOf(b))
  sort(topLevelIds)
  Object.keys(childrenOf).forEach(pid => sort(childrenOf[pid]))

  return { topLevelIds, childrenOf, full }
}

function DetailSuiteGroup({ suiteId, groups, childrenOf, updateResult }) {
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

export function ExecutionDetailPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const { data: project } = useProject(execution?.project_id)
  const { data: allSuites = [] } = useSuitesAll(execution?.project_id)
  const updateResult = useUpdateResult(id)

  const suiteByCase = useMemo(() => mapSuiteByCase(allSuites), [allSuites])
  const { groups, topLevelIds, childrenOf } = useMemo(() => {
    const groups = {}
    results.forEach(r => {
      const suite = suiteByCase[r.test_case_id]
      const key = suite?.id ?? 0
      if (!groups[key]) groups[key] = { suite: suite ?? null, items: [] }
      groups[key].items.push(r)
    })
    if (!allSuites.length || !Object.keys(groups).some(k => k !== "0")) {
      return { groups, topLevelIds: [], childrenOf: {} }
    }
    const { topLevelIds, childrenOf, full } = buildDetailTree(groups, allSuites)
    return { groups: full, topLevelIds, childrenOf }
  }, [results, allSuites, suiteByCase])

  if (!execution) {
    return (
      <div className="p-8 max-w-3xl space-y-4">
        <Skeleton className="h-7 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
        <SkeletonList count={4} itemClassName="h-12" />
      </div>
    )
  }

  const versionLabel = execution.version ?? null

  return (
    <div className="p-8 max-w-3xl space-y-6">
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
              {(execution.token_name || execution.created_by || execution.triggered_by) && (
                <span>· {execution.token_name
                  ? `via ${execution.token_name}`
                  : `by ${execution.created_by?.username ?? execution.triggered_by}`}
                </span>
              )}
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
          <div className="flex items-center gap-2 shrink-0">
            {execution.type === 'automatic' && (
              <ImportResultsButton executionId={id} />
            )}
            <Button size="sm" variant="outline" onClick={() => downloadPdf(execution, results, project?.name)}>
              <Download size={13} /> PDF
            </Button>
            <Button size="sm" variant="outline" onClick={() => executionsApi.exportHtml(id, execution.title)}>
              <Download size={13} /> HTML
            </Button>
          </div>
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

      <div className="space-y-2">
        {topLevelIds.map(suiteId => (
          <DetailSuiteGroup key={suiteId} suiteId={suiteId} groups={groups} childrenOf={childrenOf} updateResult={updateResult} />
        ))}
        {(topLevelIds.length === 0 || groups[0]) && (
          <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              {TABLE_HEAD}
              <tbody className="divide-y divide-gray-100">
                <ResultRows items={topLevelIds.length === 0 ? results : (groups[0]?.items ?? [])} updateResult={updateResult} />
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
