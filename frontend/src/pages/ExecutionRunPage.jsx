import { useState, useMemo, useEffect } from "react"
import { useParams } from "react-router-dom"
import { ExternalLink, Clock, Keyboard, User, Download, FolderOpen, ChevronRight } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { useExecution, useExecutionResults, useUpdateResult } from "../hooks/useExecutions"
import { executionsApi } from "../api/executions"
import { useProject } from "../hooks/useProjects"
import { useSuitesAll, sortSuitesHierarchically } from "../hooks/useSuites"
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { Button } from "../components/ui/button"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../components/ui/dialog"
import { ResultCard } from "../components/execution/ResultCard"
import { mapSuiteByCase } from "../components/ui/test-case-item"
import { fmtDuration } from "../lib/format"
import { STATUS_CONFIG } from "../lib/statusConfig"
import { toast } from "sonner"

async function downloadPdf(execution, results, projectName) {
  const { exportExecutionPdf } = await import('../lib/exportPdf')
  exportExecutionPdf(execution, results, projectName)
}

const SHORTCUT_TO_STATUS = { p: "passed", f: "failed", b: "blocked", n: "not_run" }

export function ExecutionRunPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const qc = useQueryClient()
  const [finishing, setFinishing] = useState(false)

  const finishExecution = async () => {
    setFinishing(true)
    try {
      await executionsApi.update(id, { status: "completed", finished_at: new Date().toISOString() })
      qc.invalidateQueries({ queryKey: ["executions", id] })
      toast.success("Execution completed")
    } catch {
      toast.error("Failed to finish execution")
      setFinishing(false)
    }
  }

  if (!execution) {
    return (
      <div className="p-8 max-w-2xl space-y-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-7 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
        <SkeletonList count={3} itemClassName="h-24" />
      </div>
    )
  }

  const summary = execution.summary ?? {}
  const done = (summary.passed ?? 0) + (summary.failed ?? 0) + (summary.blocked ?? 0)
  const totalMs = execution.started_at && execution.finished_at
    ? new Date(execution.finished_at) - new Date(execution.started_at)
    : null

  return <ExecutionRunBody {...{ execution, results, id, summary, done, totalMs, finishExecution, finishing }} />
}

function buildResultTree(groups, allSuites) {
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

function RunSuiteGroup({ suiteId, groups, childrenOf, orderedResults, focusedResultId, setFocusedResultId, id, isAutomated }) {
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
        <div className="px-2 py-2 space-y-2">
          {children.length > 0 && (
            <div className="pl-4 space-y-2 border-l-2 border-gray-100">
              {children.map(childId => (
                <RunSuiteGroup key={childId} suiteId={childId} groups={groups} childrenOf={childrenOf}
                  orderedResults={orderedResults} focusedResultId={focusedResultId} setFocusedResultId={setFocusedResultId}
                  id={id} isAutomated={isAutomated} />
              ))}
            </div>
          )}
          {items.map(result => {
            const treeIdx = orderedResults.findIndex(r => r.id === result.id)
            return (
              <ResultCard key={result.id} result={result} executionId={id} index={treeIdx} total={orderedResults.length}
                isAutomated={isAutomated}
                focused={result.id === focusedResultId}
                onFocus={() => setFocusedResultId(result.id)} />
            )
          })}
        </div>
      </details>
    </div>
  )
}

function ExecutionRunBody({ execution, results, id, summary, done, totalMs, finishExecution, finishing }) {
  const { data: project } = useProject(execution.project_id)
  const { data: allSuites = [] } = useSuitesAll(execution.project_id)
  const updateResult = useUpdateResult(id)
  const [focusedResultId, setFocusedResultId] = useState(null)
  const [helpOpen, setHelpOpen] = useState(false)
  const isAutomated = execution.type === "automatic"

  const suiteByCase = useMemo(() => mapSuiteByCase(allSuites), [allSuites])
  const { groups, topLevelIds, childrenOf, orderedResults } = useMemo(() => {
    const groups = {}
    results.forEach(r => {
      const suite = suiteByCase[r.test_case_id]
      const key = suite?.id ?? 0
      if (!groups[key]) groups[key] = { suite: suite ?? null, items: [] }
      groups[key].items.push(r)
    })
    let topLevelIds = []
    let childrenOf = {}
    let groupsFull = groups
    if (allSuites.length && Object.keys(groups).some(k => k !== "0")) {
      const built = buildResultTree(groups, allSuites)
      topLevelIds = built.topLevelIds
      childrenOf = built.childrenOf
      groupsFull = built.full
    }
    // Flatten in render order (children DFS first, then own items)
    const ordered = []
    const walk = (sid) => {
      for (const c of (childrenOf[sid] ?? [])) walk(c)
      for (const it of (groupsFull[sid]?.items ?? [])) ordered.push(it)
    }
    for (const tl of topLevelIds) walk(tl)
    for (const it of (groupsFull[0]?.items ?? [])) ordered.push(it)
    if (ordered.length === 0) ordered.push(...results)
    return { groups: groupsFull, topLevelIds, childrenOf, orderedResults: ordered }
  }, [results, allSuites, suiteByCase])

  // Auto-select first result in tree order (dives into deepest first subsuite)
  useEffect(() => {
    if (focusedResultId == null && orderedResults.length > 0) {
      setFocusedResultId(orderedResults[0].id)
    }
  }, [orderedResults, focusedResultId])

  const focused = orderedResults.find(r => r.id === focusedResultId) ?? null

  const stepBy = (delta) => {
    const idx = orderedResults.findIndex(r => r.id === focusedResultId)
    if (idx < 0) {
      if (orderedResults[0]) setFocusedResultId(orderedResults[0].id)
      return
    }
    const target = orderedResults[Math.max(0, Math.min(orderedResults.length - 1, idx + delta))]
    if (target) setFocusedResultId(target.id)
  }

  useKeyboardShortcuts({
    j: () => stepBy(1),
    ArrowDown: () => stepBy(1),
    k: () => stepBy(-1),
    ArrowUp: () => stepBy(-1),
    "?": () => setHelpOpen(o => !o),
    Escape: () => setHelpOpen(false),
    ...(isAutomated ? {} : Object.fromEntries(
      Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => [
        key,
        async () => {
          if (!focused) return
          try {
            await updateResult.mutateAsync({ id: focused.id, data: { status } })
          } catch {
            toast.error("Failed to update status")
          }
        },
      ])
    )),
  }, { enabled: orderedResults.length > 0, allowWhileTyping: ["Escape"] })

  return (
    <div className="p-8 max-w-2xl space-y-4">
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${execution.project_id}` },
          { label: "Executions", to: `/projects/${execution.project_id}/executions` },
          { label: execution.title },
        ]}
      />

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">{execution.title}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-sm text-gray-500">
            {execution.version && <span>v{execution.version}</span>}
            {execution.environment && <span>{execution.environment}</span>}
            {(execution.token_name || execution.created_by || execution.triggered_by) && (
              <span>{execution.token_name
                ? `via ${execution.token_name}`
                : `by ${execution.created_by?.username ?? execution.triggered_by}`}
              </span>
            )}
            {execution.assigned_to && (
              <span className="flex items-center gap-1">
                <User size={12} /> {execution.assigned_to.username}
              </span>
            )}
            <span>{done}/{summary.total ?? 0} done</span>
            {totalMs != null && (
              <span className="flex items-center gap-1 text-gray-400">
                <Clock size={12} /> {fmtDuration(totalMs)} total
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" onClick={() => setHelpOpen(true)} title="Keyboard shortcuts (?)">
            <Keyboard size={14} />
          </Button>
          <Button variant="outline" size="sm" onClick={() => downloadPdf(execution, results, project?.name)}>
            <Download size={13} /> PDF
          </Button>
          <Button variant="outline" size="sm" onClick={() => executionsApi.exportHtml(id, execution.title)}>
            <Download size={13} /> HTML
          </Button>
          <Button
            onClick={finishExecution}
            disabled={execution.status === "completed" || finishing}
            loading={finishing}
          >
            {execution.status === "completed" ? "Completed" : "Finish execution"}
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex gap-3 text-sm">
          <span className="text-green-600 font-medium">✓ {summary.passed ?? 0} passed</span>
          <span className="text-red-500 font-medium">✗ {summary.failed ?? 0} failed</span>
          <span className="text-yellow-600 font-medium">⚠ {summary.blocked ?? 0} blocked</span>
          <span className="text-gray-400">— {summary.not_run ?? 0} not run</span>
        </div>
        {(execution.attachments ?? []).length > 0 && (
          <div className="flex gap-2 ml-auto">
            {execution.attachments.map(a => (
              <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600 border rounded px-2 py-1 bg-white hover:bg-gray-50 transition-colors">
                <ExternalLink size={11} />{a.filename}
              </a>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        {topLevelIds.map(suiteId => (
          <RunSuiteGroup key={suiteId} suiteId={suiteId} groups={groups} childrenOf={childrenOf}
            orderedResults={orderedResults} focusedResultId={focusedResultId} setFocusedResultId={setFocusedResultId}
            id={id} isAutomated={isAutomated} />
        ))}
        {groups[0] && (
          <div className="space-y-2">
            {groups[0].items.map(result => {
              const treeIdx = orderedResults.findIndex(r => r.id === result.id)
              return (
                <ResultCard key={result.id} result={result} executionId={id} index={treeIdx} total={orderedResults.length}
                  isAutomated={isAutomated}
                  focused={result.id === focusedResultId}
                  onFocus={() => setFocusedResultId(result.id)} />
              )
            })}
          </div>
        )}
        {topLevelIds.length === 0 && !groups[0] && orderedResults.map((result, treeIdx) => (
          <ResultCard key={result.id} result={result} executionId={id} index={treeIdx} total={orderedResults.length}
            isAutomated={isAutomated}
            focused={result.id === focusedResultId}
            onFocus={() => setFocusedResultId(result.id)} />
        ))}
      </div>

      <ShortcutHelpDialog open={helpOpen} onOpenChange={setHelpOpen} isAutomated={isAutomated} />
    </div>
  )
}

function ShortcutHelpDialog({ open, onOpenChange, isAutomated }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
          <DialogDescription>Navigate and update results without the mouse.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2 text-sm">
          <ShortcutRow keys={["j", "↓"]} description="Focus next result" />
          <ShortcutRow keys={["k", "↑"]} description="Focus previous result" />
          {!isAutomated && Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => (
            <ShortcutRow key={key} keys={[key]} description={`Mark as ${STATUS_CONFIG[status].label}`} />
          ))}
          <ShortcutRow keys={["?"]} description="Toggle this help" />
          <ShortcutRow keys={["Esc"]} description="Close this help" />
        </div>
      </DialogContent>
    </Dialog>
  )
}

function ShortcutRow({ keys, description }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex gap-1">
        {keys.map(k => (
          <kbd key={k} className="px-2 py-0.5 text-xs font-mono bg-gray-100 border border-gray-300 rounded">{k}</kbd>
        ))}
      </div>
      <span className="text-gray-600">{description}</span>
    </div>
  )
}
