import { useState, useMemo, useEffect } from "react"
import { useParams, Link } from "react-router-dom"
import { ExternalLink, Clock, Keyboard, User, Download } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { useExecution, useExecutionResults, useUpdateResult } from "../hooks/useExecutions"
import { useExecutionLive } from "../hooks/useExecutionLive"
import { executionsApi } from "../api/executions"
import { useExportExecution } from "../hooks/useExportExecution"
import { useProject } from "../hooks/useProjects"
import { useSuitesAll, useCase } from "../hooks/useSuites"
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts"
import { useSwipe } from "../hooks/useSwipe"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Button } from "../components/ui/button"
import { LiveIndicator } from "../components/ui/live-indicator"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { ResultCard, ResultExpandContext } from "../components/execution/ResultCard"
import { RunSuiteGroup } from "../components/execution/RunSuiteGroup"
import { ShortcutHelpDialog, SHORTCUT_TO_STATUS } from "../components/execution/ShortcutHelpDialog"

const STATUS_FILTER_KEY = { F: "failed", B: "blocked", U: "not_run" }
import { mapSuiteByCase } from "../components/ui/test-case-item"
import { fmtDuration, fmtDateTime } from "../lib/format"
import { ContextPanel } from "../components/ui/context-panel"
import { buildResultTree } from "../lib/buildResultTree"

const EXECUTION_STATUS_PILL = {
  pending:     "bg-gray-100 text-gray-600 border-gray-200",
  in_progress: "bg-blue-50 text-blue-700 border-blue-200",
  completed:   "bg-green-50 text-green-700 border-green-200",
  aborted:     "bg-red-50 text-red-700 border-red-200",
}

const EXECUTION_TYPE_PILL = {
  manual:    "bg-amber-50 text-amber-700 border-amber-200",
  automatic: "bg-purple-50 text-purple-700 border-purple-200",
}

function StatusPill({ status }) {
  const cls = EXECUTION_STATUS_PILL[status] ?? "bg-gray-100 text-gray-600 border-gray-200"
  return <span className={`inline-block text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${cls}`}>{status?.replace("_", " ")}</span>
}

function TypePill({ type }) {
  const cls = EXECUTION_TYPE_PILL[type] ?? "bg-gray-100 text-gray-600 border-gray-200"
  return <span className={`inline-block text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${cls}`}>{type}</span>
}

function UserLink({ user }) {
  if (!user) return null
  return <Link to="/users" className="text-primary-600 hover:underline">{user.full_name || user.username}</Link>
}

function PanelExecutionAttachments({ attachments = [] }) {
  if (attachments.length === 0) return <p className="text-[11px] text-gray-400">No attachments</p>
  return (
    <ul className="space-y-1">
      {attachments.map(att => (
        <li key={att.id} className="flex items-center gap-1.5 text-xs">
          <a href={att.url} target="_blank" rel="noopener noreferrer"
            className="flex-1 min-w-0 truncate text-gray-700 hover:text-primary-600 flex items-center gap-1">
            {att.filename}
            <ExternalLink size={10} className="shrink-0 text-gray-400" />
          </a>
          {att.size_bytes != null && (
            <span className="text-[10px] text-gray-400 shrink-0">{Math.round(att.size_bytes / 1024)} KB</span>
          )}
        </li>
      ))}
    </ul>
  )
}

export function ExecutionRunPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const { connected: live } = useExecutionLive(id)
  const qc = useQueryClient()
  const [finishing, setFinishing] = useState(false)
  const { exportPdf, exportHtml } = useExportExecution()

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
      <PageBody>
        <div className="max-w-2xl space-y-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-7 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
          <SkeletonList count={3} itemClassName="h-24" />
        </div>
      </PageBody>
    )
  }

  const summary = execution.summary ?? {}
  const done = (summary.passed ?? 0) + (summary.failed ?? 0) + (summary.blocked ?? 0)
  const totalMs = execution.started_at && execution.finished_at
    ? new Date(execution.finished_at) - new Date(execution.started_at)
    : null

  return <ExecutionRunBody {...{ execution, results, id, summary, done, totalMs, finishExecution, finishing, exportPdf, exportHtml, live }} />
}

function ExecutionRunBody({ execution, results, id, summary, done, totalMs, finishExecution, finishing, exportPdf, exportHtml, live }) {
  const { data: project } = useProject(execution.project_id)
  const { data: allSuites = [] } = useSuitesAll(execution.project_id)
  const updateResult = useUpdateResult(id)
  const [focusedResultId, setFocusedResultId] = useState(null)
  const [focusedStepId, setFocusedStepId] = useState(null)
  const [helpOpen, setHelpOpen] = useState(false)
  const [followLive, setFollowLive] = useState(true)
  const [expandState, setExpandState] = useState({ version: 0, desiredOpen: null })
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

  useEffect(() => {
    if (focusedResultId == null && orderedResults.length > 0) {
      setFocusedResultId(orderedResults[0].id)
    }
  }, [orderedResults, focusedResultId])

  const runningResultId = useMemo(() => {
    for (const result of orderedResults) {
      if (result.status === "running") return result.id
      if ((result.step_results ?? []).some(sr => sr.status === "running")) return result.id
    }
    return null
  }, [orderedResults])

  const isExecutionLive = execution.status === "pending" || execution.status === "in_progress"

  useEffect(() => {
    if (runningResultId != null && followLive && isExecutionLive) {
      setFocusedResultId(runningResultId)
    }
  }, [runningResultId, followLive, isExecutionLive])

  useEffect(() => {
    const scroller = document.querySelector("main")
    if (!scroller) return undefined
    let userScrolling = false
    const onUserInteract = () => { userScrolling = true }
    const onScroll = () => {
      if (!userScrolling) return
      userScrolling = false
      if (runningResultId == null) return
      const card = document.querySelector(`[data-result-id="${runningResultId}"]`)
      if (!card) return
      const cardRect = card.getBoundingClientRect()
      const scrollerRect = scroller.getBoundingClientRect()
      const fullyVisible =
        cardRect.top >= scrollerRect.top && cardRect.bottom <= scrollerRect.bottom
      if (!fullyVisible) setFollowLive(false)
    }
    scroller.addEventListener("wheel", onUserInteract, { passive: true })
    scroller.addEventListener("touchstart", onUserInteract, { passive: true })
    scroller.addEventListener("scroll", onScroll, { passive: true })
    return () => {
      scroller.removeEventListener("wheel", onUserInteract)
      scroller.removeEventListener("touchstart", onUserInteract)
      scroller.removeEventListener("scroll", onScroll)
    }
  }, [runningResultId])

  const resumeFollowLive = () => {
    setFollowLive(true)
    if (runningResultId != null) setFocusedResultId(runningResultId)
  }

  const focused = orderedResults.find(r => r.id === focusedResultId) ?? null
  const { data: focusedCase } = useCase(focused?.test_case_id)
  const focusedSteps = focusedCase?.steps ?? []

  useEffect(() => { setFocusedStepId(null) }, [focusedResultId])

  const stepBy = (delta) => {
    const idx = orderedResults.findIndex(r => r.id === focusedResultId)
    if (idx < 0) {
      if (orderedResults[0]) setFocusedResultId(orderedResults[0].id)
      return
    }
    const target = orderedResults[Math.max(0, Math.min(orderedResults.length - 1, idx + delta))]
    if (target) setFocusedResultId(target.id)
  }

  const focusResult = (which) => {
    if (orderedResults.length === 0) return
    setFocusedResultId(which === "first"
      ? orderedResults[0].id
      : orderedResults[orderedResults.length - 1].id)
  }

  const stepNav = (delta) => {
    if (focusedSteps.length === 0) return
    const idx = focusedSteps.findIndex(s => s.id === focusedStepId)
    if (idx < 0) {
      setFocusedStepId(delta > 0 ? focusedSteps[0].id : focusedSteps[focusedSteps.length - 1].id)
      return
    }
    const next = focusedSteps[Math.max(0, Math.min(focusedSteps.length - 1, idx + delta))]
    if (next) setFocusedStepId(next.id)
  }

  const jumpToStatus = (status) => {
    if (orderedResults.length === 0) return
    const startIdx = orderedResults.findIndex(r => r.id === focusedResultId)
    const total = orderedResults.length
    for (let offset = 1; offset <= total; offset += 1) {
      const target = orderedResults[(startIdx + offset + total) % total]
      if (target.status === status) {
        setFocusedResultId(target.id)
        return
      }
    }
  }

  const toggleFocusedExpand = () => {
    if (focusedResultId == null) return
    const card = document.querySelector(`[data-result-id="${focusedResultId}"]`)
    card?.dispatchEvent(new CustomEvent("result-toggle"))
  }

  const expandAllResults = () =>
    setExpandState(s => ({ version: s.version + 1, desiredOpen: true }))
  const collapseAllResults = () =>
    setExpandState(s => ({ version: s.version + 1, desiredOpen: false }))

  const swipe = useSwipe({
    onSwipeLeft: () => stepBy(1),
    onSwipeRight: () => stepBy(-1),
  })

  useKeyboardShortcuts({
    j: () => stepBy(1),
    ArrowDown: () => stepBy(1),
    k: () => stepBy(-1),
    ArrowUp: () => stepBy(-1),
    J: () => stepNav(1),
    K: () => stepNav(-1),
    Home: () => focusResult("first"),
    End: () => focusResult("last"),
    F: () => jumpToStatus("failed"),
    B: () => jumpToStatus("blocked"),
    U: () => jumpToStatus("not_run"),
    o: toggleFocusedExpand,
    "+": expandAllResults,
    "-": collapseAllResults,
    L: () => setFollowLive(v => !v),
    r: resumeFollowLive,
    "?": () => setHelpOpen(o => !o),
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
  }, { enabled: orderedResults.length > 0 })

  const contextSections = [
    {
      title: "About",
      rows: [
        { label: "Project", value: project?.name },
        { label: "Status", value: <StatusPill status={execution.status} /> },
        { label: "Type", value: <TypePill type={execution.type} /> },
        { label: "Version", value: execution.version },
        { label: "Environment", value: execution.environment },
        { label: "Created by", value: <UserLink user={execution.created_by} /> },
        { label: "Triggered by", value: execution.triggered_by },
        { label: "Token", value: execution.token_name },
        { label: "Assigned to", value: <UserLink user={execution.assigned_to} /> },
        { label: "Created", value: fmtDateTime(execution.created_at) },
        { label: "Started", value: fmtDateTime(execution.started_at) },
        { label: "Finished", value: fmtDateTime(execution.finished_at) },
      ],
    },
    {
      title: "Summary",
      rows: [
        { label: "Total", value: summary.total ?? 0 },
        { label: "Passed", value: summary.passed ?? 0 },
        { label: "Failed", value: summary.failed ?? 0 },
        { label: "Blocked", value: summary.blocked ?? 0 },
        { label: "Not run", value: summary.not_run ?? 0 },
      ],
    },
    {
      title: `Attachments (${(execution.attachments ?? []).length})`,
      body: <PanelExecutionAttachments attachments={execution.attachments ?? []} />,
    },
  ]

  return (
    <>
      <PageHeader crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${execution.project_id}` },
        { label: "Executions", to: `/projects/${execution.project_id}/executions` },
        { label: execution.title },
      ]}>
        <div className="max-w-2xl flex flex-col gap-3 md:flex-row md:items-start md:justify-between md:gap-4">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-gray-800 break-words md:truncate flex items-center gap-2 flex-wrap">
              {execution.title}
              <LiveIndicator connected={live} />
            </h1>
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
            <div className="flex items-center gap-3 mt-1.5 text-sm">
              <span className="text-green-600 font-medium">✓ {summary.passed ?? 0} passed</span>
              <span className="text-red-500 font-medium">✗ {summary.failed ?? 0} failed</span>
              <span className="text-yellow-600 font-medium">⚠ {summary.blocked ?? 0} blocked</span>
              <span className="text-gray-400">— {summary.not_run ?? 0} not run</span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 md:shrink-0">
            <Button variant="ghost" size="sm" onClick={() => setHelpOpen(true)} title="Keyboard shortcuts (?)">
              <Keyboard size={14} />
            </Button>
            <Button variant="outline" size="sm" onClick={() => exportPdf(execution, results, project?.name)}>
              <Download size={13} /> PDF
            </Button>
            <Button variant="outline" size="sm" onClick={() => exportHtml(id, execution.title)}>
              <Download size={13} /> HTML
            </Button>
            <Button
              onClick={finishExecution}
              disabled={execution.status === "completed" || finishing}
              loading={finishing}
            >
              {execution.status === "completed" ? "Completed" : <><span className="sm:hidden">Finish</span><span className="hidden sm:inline">Finish execution</span></>}
            </Button>
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="flex gap-6" {...swipe}>
          <div className="flex-1 min-w-0 max-w-2xl space-y-4">
            <ResultExpandContext.Provider value={expandState}>
              <div className="space-y-2">
                {topLevelIds.map(suiteId => (
                  <RunSuiteGroup key={suiteId} suiteId={suiteId} groups={groups} childrenOf={childrenOf}
                    orderedResults={orderedResults} focusedResultId={focusedResultId} setFocusedResultId={setFocusedResultId}
                    id={id} isAutomated={isAutomated} focusedStepId={focusedStepId} />
                ))}
                {groups[0] && (
                  <div className="space-y-2">
                    {groups[0].items.map(result => {
                      const treeIdx = orderedResults.findIndex(r => r.id === result.id)
                      return (
                        <ResultCard key={result.id} result={result} executionId={id} index={treeIdx} total={orderedResults.length}
                          isAutomated={isAutomated}
                          focused={result.id === focusedResultId}
                          focusedStepId={result.id === focusedResultId ? focusedStepId : null}
                          onFocus={() => setFocusedResultId(result.id)} />
                      )
                    })}
                  </div>
                )}
                {topLevelIds.length === 0 && !groups[0] && orderedResults.map((result, treeIdx) => (
                  <ResultCard key={result.id} result={result} executionId={id} index={treeIdx} total={orderedResults.length}
                    isAutomated={isAutomated}
                    focused={result.id === focusedResultId}
                    focusedStepId={result.id === focusedResultId ? focusedStepId : null}
                    onFocus={() => setFocusedResultId(result.id)} />
                ))}
              </div>
            </ResultExpandContext.Provider>
          </div>
          <ContextPanel sections={contextSections} />
        </div>
      </PageBody>

      {!followLive && isExecutionLive && runningResultId != null && (
        <button
          type="button"
          onClick={resumeFollowLive}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-2 rounded-full bg-blue-600 text-white text-sm font-medium px-4 py-2 shadow-lg hover:bg-blue-700 transition-colors"
        >
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          Follow live
        </button>
      )}

      <ShortcutHelpDialog open={helpOpen} onOpenChange={setHelpOpen} isAutomated={isAutomated} />
    </>
  )
}
