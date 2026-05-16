import { useState, useMemo, useRef, useContext, useEffect } from "react"
import { useParams, Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useQuery } from "@tanstack/react-query"
import {
  Grid3x3, ChevronRight, FolderOpen, FileText,
  ChevronsUpDown, ChevronsDownUp, Keyboard,
} from "lucide-react"
import { useProject } from "../hooks/useProjects"
import { useSuitesAll } from "../hooks/useSuites"
import { useDebounced } from "../hooks/useDebounced"
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts"
import { useTreeItemNav } from "../hooks/useTreeItemNav"
import { coverageApi } from "../api/coverage"
import { Button } from "../components/ui/button"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { SkeletonList } from "../components/ui/skeleton"
import { EmptyState } from "../components/ui/empty-state"
import { ShortcutsDialog } from "../components/ui/shortcuts-dialog"
import { SuiteCollapseContext } from "../components/project/SuiteRow"

const CELL_STYLE = {
  passed:  "bg-green-100  dark:bg-green-900/40  text-green-800  dark:text-green-200",
  failed:  "bg-red-100    dark:bg-red-900/40    text-red-800    dark:text-red-200",
  blocked: "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200",
  not_run: "bg-gray-50    dark:bg-gray-900      text-gray-500   dark:text-gray-400",
}
const CELL_GLYPH = { passed: "✓", failed: "✗", blocked: "⚠", not_run: "—" }
const INDENT_PX = 16
const BASE_PADDING = 12

function buildShortcutSections(t) {
  return [
    {
      title: t("coverage.shortcutSections.navigation"),
      rows: [
        { keys: ["j", "↓"], description: t("coverage.shortcutRows.next") },
        { keys: ["k", "↑"], description: t("coverage.shortcutRows.prev") },
        { keys: ["h", "←"], description: t("coverage.shortcutRows.collapse") },
        { keys: ["l", "→"], description: t("coverage.shortcutRows.expand") },
        { keys: ["PgDn"], description: t("coverage.shortcutRows.nextSuite") },
        { keys: ["PgUp"], description: t("coverage.shortcutRows.prevSuite") },
        { keys: ["Home"], description: t("coverage.shortcutRows.first") },
        { keys: ["End"], description: t("coverage.shortcutRows.last") },
        { keys: ["Enter"], description: t("coverage.shortcutRows.toggle") },
      ],
    },
    {
      title: t("coverage.shortcutSections.actions"),
      rows: [
        { keys: ["+"], description: t("coverage.shortcutRows.expandAll") },
        { keys: ["-"], description: t("coverage.shortcutRows.collapseAll") },
        { keys: ["/"], description: t("coverage.shortcutRows.focusFilter") },
        { keys: ["?"], description: t("coverage.shortcutRows.help") },
      ],
    },
  ]
}

function buildSuiteTree(allSuites, matrixCases) {
  const nodeById = new Map()
  for (const suite of allSuites) {
    nodeById.set(suite.id, {
      id: suite.id,
      name: suite.name,
      parentSuiteId: suite.parent_suite_id,
      children: [],
      cases: [],
    })
  }
  const roots = []
  for (const node of nodeById.values()) {
    if (node.parentSuiteId == null) roots.push(node)
    else nodeById.get(node.parentSuiteId)?.children.push(node)
  }
  for (const testCase of matrixCases) {
    nodeById.get(testCase.suite_id)?.cases.push(testCase)
  }
  return roots
}

function collectCases(node, acc = []) {
  acc.push(...node.cases)
  for (const child of node.children) collectCases(child, acc)
  return acc
}

function suiteMatchesQuery(node, query) {
  if (!query) return true
  if (node.name.toLowerCase().includes(query)) return true
  if (node.cases.some(testCase => testCase.name.toLowerCase().includes(query))) return true
  return node.children.some(child => suiteMatchesQuery(child, query))
}

function aggregateCells(cases, versionId, cellByKey) {
  let passed = 0, failed = 0, blocked = 0, missing = 0
  for (const testCase of cases) {
    const cell = cellByKey.get(`${testCase.id}:${versionId}`)
    if (!cell) { missing++; continue }
    if (cell.status === "passed") passed++
    else if (cell.status === "failed") failed++
    else if (cell.status === "blocked") blocked++
  }
  return { passed, failed, blocked, missing, total: cases.length }
}

function AggregatedCell({ aggregation }) {
  if (aggregation.total === 0) {
    return <span className="text-gray-400 dark:text-gray-500 text-xs">—</span>
  }
  let bgClass = CELL_STYLE.not_run
  if (aggregation.failed > 0) bgClass = CELL_STYLE.failed
  else if (aggregation.blocked > 0) bgClass = CELL_STYLE.blocked
  else if (aggregation.passed > 0 && aggregation.missing === 0) bgClass = CELL_STYLE.passed
  return (
    <span className={`inline-flex items-center justify-center rounded text-xs w-full px-2 py-1 ${bgClass}`}>
      {aggregation.passed}/{aggregation.total}
    </span>
  )
}

function CaseRow({ testCase, depth, versions, cellByKey, suiteId }) {
  const { t } = useTranslation(["versions", "common"])
  const handleKeyDown = useTreeItemNav({
    onCollapse: () => {
      const parent = document.querySelector(`[data-treeitem-kind="suite"][data-suite-id="${suiteId}"]`)
      parent?.focus()
    },
  })
  const paddingLeft = BASE_PADDING + depth * INDENT_PX
  return (
    <tr
      role="treeitem"
      tabIndex={0}
      data-treeitem-kind="case"
      data-case-id={testCase.id}
      onKeyDown={handleKeyDown}
      className="group/row hover:bg-blue-50 dark:hover:bg-blue-900/30 focus:bg-blue-50 dark:focus:bg-blue-900/30 focus:outline-none"
    >
      <th scope="row" className="sticky left-0 z-10 bg-white dark:bg-gray-900 group-hover/row:bg-blue-50 dark:group-hover/row:bg-blue-900/30 group-focus/row:bg-blue-50 dark:group-focus/row:bg-blue-900/30 px-3 py-1.5 text-left font-normal border-b" style={{ paddingLeft }}>
        <Link to={`/cases/${testCase.id}`} className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-200 hover:underline">
          <FileText size={12} className="text-gray-400 dark:text-gray-500 shrink-0" />
          <span className="truncate">{testCase.name}</span>
        </Link>
      </th>
      {versions.map(version => {
        const cell = cellByKey.get(`${testCase.id}:${version.id}`)
        const status = cell?.status ?? "not_run"
        const style = CELL_STYLE[status]
        const glyph = CELL_GLYPH[status]
        const label = t(`common:status.${status}`, status)
        return (
          <td key={version.id} className="border-l border-b text-center px-1 py-1">
            {cell ? (
              <Link
                to={`/executions/${cell.execution_id}/run`}
                className={`inline-flex items-center justify-center rounded w-full px-2 py-1 ${style}`}
                title={label}
              >
                {glyph}
              </Link>
            ) : (
              <span className={`inline-flex items-center justify-center rounded w-full px-2 py-1 ${CELL_STYLE.not_run}`}>—</span>
            )}
          </td>
        )
      })}
    </tr>
  )
}

function SuiteRow({ suite, depth, versions, cellByKey, query }) {
  const { version, desiredOpen } = useContext(SuiteCollapseContext)
  const [open, setOpen] = useState(desiredOpen)
  useEffect(() => { if (version > 0) setOpen(desiredOpen) }, [version, desiredOpen])
  const toggleOpen = () => setOpen(value => !value)
  const handleKeyDown = useTreeItemNav({
    onCollapse: () => { if (open) setOpen(false) },
    onExpand: () => { if (!open) setOpen(true) },
    onActivate: toggleOpen,
    onToggleSelect: toggleOpen,
    ignoreUnlessSelfTarget: true,
  })

  if (!suiteMatchesQuery(suite, query)) return null

  const isOpen = query ? true : open
  const descendantCases = useMemo(() => collectCases(suite), [suite])
  const visibleCases = query
    ? suite.cases.filter(testCase => testCase.name.toLowerCase().includes(query))
    : suite.cases
  const paddingLeft = BASE_PADDING + depth * INDENT_PX

  return (
    <>
      <tr
        role="treeitem"
        tabIndex={0}
        aria-expanded={isOpen}
        data-treeitem-kind="suite"
        data-suite-id={suite.id}
        onKeyDown={handleKeyDown}
        onClick={toggleOpen}
        className="group/row bg-gray-50/60 dark:bg-gray-800/30 hover:bg-blue-50 dark:hover:bg-blue-900/30 focus:bg-blue-50 dark:focus:bg-blue-900/30 cursor-pointer focus:outline-none"
      >
        <th scope="row" className="sticky left-0 z-10 bg-gray-50/60 dark:bg-gray-800/30 group-hover/row:bg-blue-50 dark:group-hover/row:bg-blue-900/30 group-focus/row:bg-blue-50 dark:group-focus/row:bg-blue-900/30 px-3 py-1.5 text-left font-medium border-b" style={{ paddingLeft }}>
          <div className="flex items-center gap-1.5 text-sm text-gray-800 dark:text-gray-100">
            <ChevronRight size={13} className={`transition-transform shrink-0 ${isOpen ? "rotate-90" : ""}`} />
            <FolderOpen size={13} className="text-yellow-500 shrink-0" />
            <span className="truncate">{suite.name}</span>
            <span className="text-[11px] text-gray-400 dark:text-gray-500 shrink-0">({descendantCases.length})</span>
          </div>
        </th>
        {versions.map(version => (
          <td key={version.id} className="border-l border-b text-center px-1 py-1">
            <AggregatedCell aggregation={aggregateCells(descendantCases, version.id, cellByKey)} />
          </td>
        ))}
      </tr>
      {isOpen && (
        <>
          {suite.children.map(child => (
            <SuiteRow key={child.id} suite={child} depth={depth + 1} versions={versions} cellByKey={cellByKey} query={query} />
          ))}
          {visibleCases.map(testCase => (
            <CaseRow key={testCase.id} testCase={testCase} depth={depth + 1} versions={versions} cellByKey={cellByKey} suiteId={suite.id} />
          ))}
        </>
      )}
    </>
  )
}

export function CoverageMatrixPage() {
  const { t } = useTranslation(["versions", "nav", "common"])
  const { id: projectId } = useParams()
  const [includeArchived, setIncludeArchived] = useState(false)
  const [filter, setFilter] = useState("")
  const debouncedFilter = useDebounced(filter, 150)
  const [collapseState, setCollapseState] = useState({ version: 0, desiredOpen: true })
  const [helpOpen, setHelpOpen] = useState(false)
  const filterRef = useRef(null)
  const tableContainerRef = useRef(null)
  const lastFocusedRowRef = useRef(null)
  const { data: project } = useProject(projectId)
  const { data: suites = [] } = useSuitesAll(projectId)
  const { data, isLoading } = useQuery({
    queryKey: ["coverage", projectId, { include_archived: includeArchived }],
    queryFn: () => coverageApi.matrix(projectId, { include_archived: includeArchived }),
    enabled: !!projectId,
  })

  const versions = data?.versions ?? []
  const cells = data?.cells ?? []
  const cases = data?.cases ?? []

  const cellByKey = useMemo(() => {
    const map = new Map()
    for (const cell of cells) map.set(`${cell.case_id}:${cell.version_id}`, cell)
    return map
  }, [cells])

  const tree = useMemo(() => buildSuiteTree(suites, cases), [suites, cases])
  const query = debouncedFilter.trim().toLowerCase()

  const expandAll = () => setCollapseState(state => ({ version: state.version + 1, desiredOpen: true }))
  const collapseAll = () => setCollapseState(state => ({ version: state.version + 1, desiredOpen: false }))

  const focusTreeitem = (which) => {
    const items = tableContainerRef.current?.querySelectorAll('[role="treeitem"]')
    if (!items?.length) return
    const target = which === "first" ? items[0] : items[items.length - 1]
    target.focus()
  }

  const focusSuiteRow = (delta) => {
    const container = tableContainerRef.current
    if (!container) return
    const suiteEls = Array.from(container.querySelectorAll('[data-treeitem-kind="suite"]'))
    if (!suiteEls.length) return
    const active = document.activeElement
    const currentIdx = suiteEls.indexOf(active)
    if (currentIdx >= 0) {
      const target = suiteEls[Math.max(0, Math.min(suiteEls.length - 1, currentIdx + delta))]
      target.focus()
      return
    }
    const allItems = Array.from(container.querySelectorAll('[role="treeitem"]'))
    const activeIdx = allItems.indexOf(active)
    if (activeIdx < 0) {
      suiteEls[delta > 0 ? 0 : suiteEls.length - 1].focus()
      return
    }
    if (delta > 0) (suiteEls.find(s => allItems.indexOf(s) > activeIdx) ?? suiteEls[suiteEls.length - 1]).focus()
    else ([...suiteEls].reverse().find(s => allItems.indexOf(s) < activeIdx) ?? suiteEls[0]).focus()
  }

  const handleBodyClick = (event) => {
    if (event.target.closest('[role="treeitem"], a, button, input, select, textarea, label')) return
    const items = tableContainerRef.current?.querySelectorAll('[role="treeitem"]')
    if (!items?.length) return
    const stored = lastFocusedRowRef.current
    const fallback = stored && tableContainerRef.current?.contains(stored) ? stored : items[0]
    fallback.focus()
  }

  const handleBodyFocusIn = (event) => {
    if (event.target.matches?.('[role="treeitem"]')) lastFocusedRowRef.current = event.target
  }

  useKeyboardShortcuts({
    Home: () => focusTreeitem("first"),
    End: () => focusTreeitem("last"),
    PageUp: () => focusSuiteRow(-1),
    PageDown: () => focusSuiteRow(1),
    "+": expandAll,
    "-": collapseAll,
    "/": () => { filterRef.current?.focus(); filterRef.current?.select?.() },
    "?": () => setHelpOpen(open => !open),
  })

  const isEmpty = !isLoading && (versions.length === 0 || tree.length === 0)

  return (
    <>
      <PageHeader crumbs={[
        { label: t("nav:global.projects"), to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: t("title"), to: `/projects/${projectId}/versions` },
        { label: t("coverage.title") },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("coverage.title")}</h1>
            <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
              <input type="checkbox" checked={includeArchived} onChange={event => setIncludeArchived(event.target.checked)} />
              {t("coverage.includeArchived")}
            </label>
          </div>
          <div className="flex items-center gap-2">
            <SearchInput ref={filterRef} value={filter} onChange={setFilter}
              placeholder={t("coverage.filterPlaceholder")} className="flex-1" />
            <div className="flex gap-1 shrink-0">
              <Button size="sm" variant="outline" onClick={expandAll} title={t("coverage.expandAll")}>
                <ChevronsUpDown size={13} />
              </Button>
              <Button size="sm" variant="outline" onClick={collapseAll} title={t("coverage.collapseAll")}>
                <ChevronsDownUp size={13} />
              </Button>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setHelpOpen(true)} title={t("coverage.shortcutsButton")}>
              <Keyboard size={14} />
            </Button>
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-full" onClick={handleBodyClick} onFocus={handleBodyFocusIn}>
          {isLoading ? (
            <SkeletonList count={4} />
          ) : isEmpty ? (
            <EmptyState
              icon={Grid3x3}
              title={t("coverage.emptyTitle")}
              description={t("coverage.emptyDescription")}
              compact
            />
          ) : (
            <SuiteCollapseContext.Provider value={collapseState}>
              <div ref={tableContainerRef} className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-900">
                <table className="text-sm border-collapse" role="tree" aria-label={t("coverage.title")}>
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-800/60">
                      <th className="sticky left-0 z-20 bg-gray-50 dark:bg-gray-800/60 px-3 py-2 text-left font-medium text-gray-600 dark:text-gray-300 border-b min-w-[260px]">
                        {t("coverage.caseColumn")}
                      </th>
                      {versions.map(version => (
                        <th key={version.id} className="px-2 py-2 text-left font-medium text-gray-700 dark:text-gray-200 border-b border-l w-[72px]">
                          <Link
                            to={`/projects/${projectId}/versions/${version.id}`}
                            className="hover:underline truncate block"
                            title={t("openDetail")}
                          >
                            {version.name}
                          </Link>
                          <div className="text-[10px] font-normal text-gray-400 dark:text-gray-500 uppercase">
                            {t(`statuses.${version.status}`)}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tree.map(rootSuite => (
                      <SuiteRow
                        key={rootSuite.id}
                        suite={rootSuite}
                        depth={0}
                        versions={versions}
                        cellByKey={cellByKey}
                        query={query}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </SuiteCollapseContext.Provider>
          )}
        </div>
      </PageBody>

      <ShortcutsDialog
        open={helpOpen}
        onOpenChange={setHelpOpen}
        description={t("coverage.shortcutsDescription")}
        sections={buildShortcutSections(t)}
      />
    </>
  )
}
