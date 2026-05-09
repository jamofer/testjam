import { useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { Upload, Tag, Clock, Download } from 'lucide-react'
import { MdViewer } from '../components/MdEditor'
import { useExecution, useExecutionResults, useUpdateResult } from '../hooks/useExecutions'
import { useExportExecution } from '../hooks/useExportExecution'
import { useProject } from '../hooks/useProjects'
import { useSuitesAll } from '../hooks/useSuites'
import { mapSuiteByCase } from '../components/ui/test-case-item'
import { Button } from '../components/ui/button'
import { Skeleton, SkeletonList } from '../components/ui/skeleton'
import { ImportResultsButton } from '../components/execution/ImportResultsButton'
import {
  DetailSuiteGroup,
  ResultRows,
  TABLE_HEAD,
} from '../components/execution/DetailSuiteGroup'
import { buildResultTree } from '../lib/buildResultTree'

function fmtDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

export function ExecutionDetailPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const { data: project } = useProject(execution?.project_id)
  const { data: allSuites = [] } = useSuitesAll(execution?.project_id)
  const updateResult = useUpdateResult(id)
  const { exportPdf, exportHtml } = useExportExecution()

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
    const { topLevelIds, childrenOf, full } = buildResultTree(groups, allSuites)
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
            <Button size="sm" variant="outline" onClick={() => exportPdf(execution, results, project?.name)}>
              <Download size={13} /> PDF
            </Button>
            <Button size="sm" variant="outline" onClick={() => exportHtml(id, execution.title)}>
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
