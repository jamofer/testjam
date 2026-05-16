import { useState, useMemo, useRef } from "react"
import { Link, useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Plus, FolderOpen, PlayCircle, Clock, FileText, Search, ChevronsUpDown, ChevronsDownUp, Keyboard, Download } from "lucide-react"
import { projectsApi } from "../api/projects"
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { useProject } from "../hooks/useProjects"
import { useSuites, useSuitesAll, useCreateSuite, useSearchCases, useReorderProjectSuites } from "../hooks/useSuites"
import { useDebounced } from "../hooks/useDebounced"
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { EmptyState } from "../components/ui/empty-state"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { ShortcutsDialog } from "../components/ui/shortcuts-dialog"
import { SuiteRow, SuiteCollapseContext } from "../components/project/SuiteRow"
import { toast } from "sonner"

function buildShortcutSections(t) {
  return [
    {
      title: t("shortcutSections.navigation"),
      rows: [
        { keys: ["j", "↓"], description: t("shortcutRows.next") },
        { keys: ["k", "↑"], description: t("shortcutRows.prev") },
        { keys: ["h", "←"], description: t("shortcutRows.collapseSuite") },
        { keys: ["l", "→"], description: t("shortcutRows.expandSuite") },
        { keys: ["Home"], description: t("shortcutRows.first") },
        { keys: ["End"], description: t("shortcutRows.last") },
        { keys: ["PgDn"], description: t("shortcutRows.nextSuite") },
        { keys: ["PgUp"], description: t("shortcutRows.prevSuite") },
        { keys: ["Enter"], description: t("shortcutRows.open") },
      ],
    },
    {
      title: t("shortcutSections.selection"),
      rows: [{ keys: ["Space", "x"], description: t("shortcutRows.toggleCheckbox") }],
    },
    {
      title: t("shortcutSections.actions"),
      rows: [
        { keys: ["+"], description: t("shortcutRows.expandAll") },
        { keys: ["-"], description: t("shortcutRows.collapseAll") },
        { keys: ["/"], description: t("shortcutRows.focusSearch") },
        { keys: ["?"], description: t("shortcutRows.toggleHelp") },
      ],
    },
  ]
}

function SortableSuite({ suite, projectId }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: suite.id, activationConstraint: { distance: 5 } })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.55 : 1,
  }
  return (
    <div ref={setNodeRef} style={style}>
      <SuiteRow suite={suite} projectId={projectId} dragHandleProps={{ ...attributes, ...listeners }} />
    </div>
  )
}

function ExportProjectButton({ projectId }) {
  const { t } = useTranslation("suites")
  const [downloading, setDownloading] = useState(false)
  const handle = async () => {
    setDownloading(true)
    try {
      await projectsApi.exportZip(projectId)
      toast.success(t("exported"))
    } catch {
      toast.error(t("exportFailed"))
    } finally {
      setDownloading(false)
    }
  }
  return (
    <Button size="sm" variant="outline" onClick={handle} loading={downloading} title={t("exportTitle")}>
      <Download size={14} /> {t("export")}
    </Button>
  )
}

function CreateSuiteDialog({ projectId }) {
  const { t } = useTranslation("suites")
  const createSuite = useCreateSuite(projectId)
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")

  const submit = async (event) => {
    event.preventDefault()
    if (!name.trim()) return
    await createSuite.mutateAsync({ name: name.trim() })
    toast.success(t("created"))
    setName("")
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus size={14} /> {t("newSuite")}</Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader><DialogTitle>{t("newSuiteTitle")}</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <Input autoFocus placeholder={t("suiteName")} value={name}
            onChange={event => setName(event.target.value)} />
          <Button type="submit" className="w-full" disabled={!name.trim() || createSuite.isPending}>
            {t("createSuite")}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function SuitesPage() {
  const { t } = useTranslation(["suites", "nav"])
  const { id } = useParams()
  const { data: project } = useProject(id)
  const { data: suites = [], isLoading } = useSuites(id)
  const reorderSuites = useReorderProjectSuites(id)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebounced(search, 200)
  const { data: searchResults = [], isFetching: searching } = useSearchCases(id, { q: debouncedSearch })
  const isSearching = debouncedSearch.trim().length > 0
  const { data: allSuites = [] } = useSuitesAll(id)
  const suitePathById = useMemo(() => {
    const byId = new Map(allSuites.map(suite => [suite.id, suite]))
    const cache = new Map()
    const climb = (suiteId) => {
      if (cache.has(suiteId)) return cache.get(suiteId)
      const suite = byId.get(suiteId)
      if (!suite) { cache.set(suiteId, []); return [] }
      const parent = suite.parent_suite_id ? climb(suite.parent_suite_id) : []
      const path = [...parent, suite.name]
      cache.set(suiteId, path)
      return path
    }
    const out = {}
    for (const suite of allSuites) out[suite.id] = climb(suite.id)
    return out
  }, [allSuites])
  const [collapseState, setCollapseState] = useState({ version: 0, desiredOpen: true })
  const expandAll = () => setCollapseState(state => ({ version: state.version + 1, desiredOpen: true }))
  const collapseAll = () => setCollapseState(state => ({ version: state.version + 1, desiredOpen: false }))
  const searchRef = useRef(null)
  const [helpOpen, setHelpOpen] = useState(false)

  const focusTreeitem = (which) => {
    const items = document.querySelectorAll('[role="treeitem"]')
    if (!items.length) return
    const target = which === "first" ? items[0] : items[items.length - 1]
    target.focus()
  }

  const focusSuite = (delta) => {
    const suiteEls = Array.from(document.querySelectorAll('[data-treeitem-kind="suite"]'))
    if (!suiteEls.length) return
    const active = document.activeElement
    const currentIdx = suiteEls.indexOf(active)
    if (currentIdx >= 0) {
      const target = suiteEls[Math.max(0, Math.min(suiteEls.length - 1, currentIdx + delta))]
      target.focus()
      return
    }
    const all = Array.from(document.querySelectorAll('[role="treeitem"]'))
    const activeIdx = all.indexOf(active)
    if (activeIdx < 0) {
      suiteEls[delta > 0 ? 0 : suiteEls.length - 1].focus()
      return
    }
    if (delta > 0) (suiteEls.find(s => all.indexOf(s) > activeIdx) ?? suiteEls[suiteEls.length - 1]).focus()
    else ([...suiteEls].reverse().find(s => all.indexOf(s) < activeIdx) ?? suiteEls[0]).focus()
  }

  useKeyboardShortcuts({
    Home: () => focusTreeitem("first"),
    End: () => focusTreeitem("last"),
    PageUp: () => focusSuite(-1),
    PageDown: () => focusSuite(1),
    "+": expandAll,
    "-": collapseAll,
    "/": () => { searchRef.current?.focus(); searchRef.current?.select?.() },
    "?": () => setHelpOpen(open => !open),
  })

  if (isLoading) {
    return (
      <PageBody>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-4">
          <Skeleton className="h-7 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
          <SkeletonList count={3} itemClassName="h-12" />
        </div>
      </PageBody>
    )
  }

  const suiteCount = project?.suite_count ?? 0
  const caseCount = project?.case_count ?? 0
  const execCount = project?.execution_count ?? 0

  return (
    <>
      <PageHeader crumbs={[{ label: t("nav:global.projects"), to: "/projects" }, { label: project?.name ?? "…", to: `/projects/${id}` }, { label: t("title") }]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between md:gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 break-words md:truncate">{project?.name}</h1>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5 text-xs text-gray-400 dark:text-gray-500">
                <span className="flex items-center gap-1">
                  <FolderOpen size={12} />
                  {t("stats.suite", { count: suiteCount })} · {t("stats.case", { count: caseCount })}
                </span>
                <span className="flex items-center gap-1">
                  <PlayCircle size={12} />
                  {t("stats.execution", { count: execCount })}
                </span>
                {project?.last_execution_at && (
                  <span className="flex items-center gap-1">
                    <Clock size={10} />
                    {new Date(project.last_execution_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ExportProjectButton projectId={id} />
              <CreateSuiteDialog projectId={id} />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <SearchInput ref={searchRef} value={search} onChange={setSearch}
              placeholder={t("searchPlaceholder")} className="flex-1" />
            {!isSearching && suites.length > 0 && (
              <div className="flex gap-1 shrink-0">
                <Button size="sm" variant="outline" onClick={expandAll} title={t("expandAll")}>
                  <ChevronsUpDown size={13} />
                </Button>
                <Button size="sm" variant="outline" onClick={collapseAll} title={t("collapseAll")}>
                  <ChevronsDownUp size={13} />
                </Button>
              </div>
            )}
            <Button size="sm" variant="ghost" onClick={() => setHelpOpen(true)} title={t("shortcuts")}>
              <Keyboard size={14} />
            </Button>
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-4">
          {isSearching ? (
            <div className="space-y-2">
              {searching && searchResults.length === 0 ? (
                <SkeletonList count={3} itemClassName="h-10" />
              ) : searchResults.length === 0 ? (
                <EmptyState
                  icon={Search}
                  title={t("search.noMatchesTitle")}
                  description={t("search.noMatchesDescription", { query: debouncedSearch })}
                />
              ) : (
                <ul className="divide-y divide-gray-100 border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900">
                  {searchResults.map(tc => {
                    const path = suitePathById[tc.suite_id] ?? []
                    return (
                      <li key={tc.id}>
                        <Link
                          to={`/cases/${tc.id}`}
                          className="flex items-start gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          <FileText size={14} className="text-gray-400 dark:text-gray-500 mt-0.5 shrink-0" />
                          <div className="min-w-0 flex-1">
                            {path.length > 0 && (
                              <div className="flex items-center flex-wrap gap-0.5 text-[11px] text-gray-400 dark:text-gray-500 mb-0.5">
                                <FolderOpen size={10} className="text-gray-300 dark:text-gray-600 shrink-0" />
                                {path.map((seg, idx) => (
                                  <span key={idx} className="flex items-center gap-0.5">
                                    {idx > 0 && <span className="text-gray-300 dark:text-gray-600">/</span>}
                                    <span className="truncate max-w-[140px]">{seg}</span>
                                  </span>
                                ))}
                              </div>
                            )}
                            <div className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{tc.name}</div>
                            {tc.description && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{tc.description}</div>
                            )}
                            {tc.tags && tc.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {tc.tags.map(tag => (
                                  <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          ) : (
            <SuiteCollapseContext.Provider value={collapseState}>
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={(event) => {
                  const { active, over } = event
                  if (!over || active.id === over.id) return
                  const oldIdx = suites.findIndex(suite => suite.id === active.id)
                  const newIdx = suites.findIndex(suite => suite.id === over.id)
                  if (oldIdx < 0 || newIdx < 0) return
                  const next = [...suites]
                  const [moved] = next.splice(oldIdx, 1)
                  next.splice(newIdx, 0, moved)
                  reorderSuites.mutate({ suiteIds: next.map(suite => suite.id), parentSuiteId: null })
                }}
              >
                <SortableContext items={suites.map(suite => suite.id)} strategy={verticalListSortingStrategy}>
                  <div className="space-y-2" role="tree" aria-label={t("tree.ariaLabel")}>
                    {suites.map(suite => <SortableSuite key={suite.id} suite={suite} projectId={id} />)}
                    {suites.length === 0 && (
                      <EmptyState
                        icon={FolderOpen}
                        title={t("tree.emptyTitle")}
                        description={t("tree.emptyDescription")}
                      />
                    )}
                  </div>
                </SortableContext>
              </DndContext>
            </SuiteCollapseContext.Provider>
          )}
        </div>
      </PageBody>

      <ShortcutsDialog open={helpOpen} onOpenChange={setHelpOpen}
        description={t("shortcutsDescription")}
        sections={buildShortcutSections(t)} />
    </>
  )
}
