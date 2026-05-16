import { useEffect, useMemo, useState } from "react"
import { useNavigate, useMatch } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Search, FolderOpen, FileText, PlayCircle, Plus, ClipboardList, Tag, Shield, Grid3x3 } from "lucide-react"
import { useProjects } from "../../hooks/useProjects"
import { useExecutions } from "../../hooks/useExecutions"
import { useSearchCases } from "../../hooks/useSuites"
import { useDebounced } from "../../hooks/useDebounced"
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./dialog"

function useActiveProjectIdFromUrl() {
  const m1 = useMatch("/projects/:id")
  const m2 = useMatch("/projects/:id/*")
  return (m1 ?? m2)?.params?.id ?? null
}

function Item({ icon: Icon, title, hint, onSelect, active, onMouseEnter }) {
  return (
    <li
      role="option"
      aria-selected={active}
      onMouseEnter={onMouseEnter}
      onClick={onSelect}
      className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer text-sm ${
        active ? "bg-primary-50 text-primary-700" : "text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
      }`}
    >
      <Icon size={14} className={active ? "text-primary-600" : "text-gray-400 dark:text-gray-500"} />
      <span className="flex-1 truncate">{title}</span>
      {hint && <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">{hint}</span>}
    </li>
  )
}

function Group({ label, children }) {
  return (
    <div className="mb-1">
      <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">{label}</div>
      <ul role="listbox">{children}</ul>
    </div>
  )
}

export function CommandPalette({ open, onOpenChange, onAction }) {
  const { t } = useTranslation("ui")
  const navigate = useNavigate()
  const activeProjectId = useActiveProjectIdFromUrl()
  const [q, setQ] = useState("")
  const [cursor, setCursor] = useState(0)
  const debouncedQ = useDebounced(q, 150)

  const { data: projects = [] } = useProjects()
  const { data: searchResults = [] } = useSearchCases(activeProjectId, { q: debouncedQ })
  const { data: execPages } = useExecutions(activeProjectId)
  const recentExecutions = useMemo(() => (execPages?.pages?.[0] ?? []).slice(0, 5), [execPages])

  const ql = q.trim().toLowerCase()
  const filteredProjects = useMemo(() => {
    if (!ql) return projects.slice(0, 8)
    return projects.filter(p => p.name.toLowerCase().includes(ql)).slice(0, 8)
  }, [projects, ql])

  const filteredExecutions = useMemo(() => {
    if (!recentExecutions.length) return []
    if (!ql) return recentExecutions
    return recentExecutions.filter(ex => ex.title.toLowerCase().includes(ql))
  }, [recentExecutions, ql])

  const filteredCases = activeProjectId && ql ? searchResults.slice(0, 8) : []

  const actions = useMemo(() => {
    if (!activeProjectId) return []
    const all = [
      {
        key: "new-exec",
        title: t("commandPalette.actions.newExecution"),
        icon: PlayCircle,
        run: () => navigate(`/projects/${activeProjectId}/executions/new`),
      },
      {
        key: "new-suite",
        title: t("commandPalette.actions.newSuite"),
        icon: Plus,
        run: () => { onAction?.("new-suite", { projectId: activeProjectId }); navigate(`/projects/${activeProjectId}`) },
      },
      {
        key: "go-plans",
        title: t("commandPalette.actions.goToPlans"),
        icon: ClipboardList,
        run: () => navigate(`/projects/${activeProjectId}/plans`),
      },
      {
        key: "go-versions",
        title: t("commandPalette.actions.goToVersions"),
        icon: Tag,
        run: () => navigate(`/projects/${activeProjectId}/versions`),
      },
      {
        key: "go-coverage",
        title: t("commandPalette.actions.goToCoverage"),
        icon: Grid3x3,
        run: () => navigate(`/projects/${activeProjectId}/coverage`),
      },
      {
        key: "go-members",
        title: t("commandPalette.actions.goToMembers"),
        icon: Shield,
        run: () => navigate(`/projects/${activeProjectId}/members`),
      },
    ]
    if (!ql) return all
    return all.filter(action => action.title.toLowerCase().includes(ql))
  }, [activeProjectId, navigate, onAction, ql, t])

  // Flat list of selectable items in render order
  const items = useMemo(() => {
    const flat = []
    filteredProjects.forEach(p => flat.push({
      kind: "project", id: `p-${p.id}`, title: p.name, icon: FolderOpen,
      hint: t("commandPalette.hints.cases", { count: p.case_count ?? 0 }),
      run: () => navigate(`/projects/${p.id}`),
    }))
    filteredExecutions.forEach(ex => flat.push({
      kind: "exec", id: `e-${ex.id}`, title: ex.title, icon: PlayCircle,
      hint: ex.status,
      run: () => navigate(`/executions/${ex.id}/run`),
    }))
    filteredCases.forEach(tc => flat.push({
      kind: "case", id: `c-${tc.id}`, title: tc.name, icon: FileText,
      hint: tc.tags?.length ? tc.tags.slice(0, 2).join(", ") : null,
      run: () => navigate(`/cases/${tc.id}`),
    }))
    actions.forEach(a => flat.push({
      kind: "action", id: `a-${a.key}`, title: a.title, icon: a.icon,
      run: a.run,
    }))
    return flat
  }, [filteredProjects, filteredExecutions, filteredCases, actions, navigate, t])

  useEffect(() => { setCursor(0) }, [q, items.length])

  // Reset on open
  useEffect(() => {
    if (open) { setQ(""); setCursor(0) }
  }, [open])

  const close = () => onOpenChange(false)
  const choose = (idx) => {
    const it = items[idx]
    if (!it) return
    it.run()
    close()
  }

  const onKey = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setCursor(c => Math.min(c + 1, items.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setCursor(c => Math.max(c - 1, 0))
    } else if (e.key === "Enter") {
      e.preventDefault()
      choose(cursor)
    }
  }

  // Track group boundaries to render labels
  let i = 0
  const renderGroup = (label, slice) => {
    if (!slice.length) return null
    const start = i
    i += slice.length
    return (
      <Group label={label} key={label}>
        {slice.map((it, j) => {
          const idx = start + j
          return (
            <Item key={it.id} {...it} active={idx === cursor}
              onSelect={() => choose(idx)}
              onMouseEnter={() => setCursor(idx)} />
          )
        })}
      </Group>
    )
  }

  const projectItems = items.filter(x => x.kind === "project")
  const execItems = items.filter(x => x.kind === "exec")
  const caseItems = items.filter(x => x.kind === "case")
  const actionItems = items.filter(x => x.kind === "action")

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl p-0 gap-0 top-[20%] translate-y-0">
        <DialogTitle className="sr-only">{t("commandPalette.title")}</DialogTitle>
        <DialogDescription className="sr-only">{t("commandPalette.description")}</DialogDescription>
        <div className="flex items-center gap-2 px-3 border-b border-gray-200 dark:border-gray-700">
          <Search size={15} className="text-gray-400 dark:text-gray-500 shrink-0" />
          <input
            autoFocus
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={onKey}
            placeholder={t("commandPalette.placeholder")}
            className="flex-1 py-3 text-sm bg-transparent focus:outline-none"
          />
          <kbd className="text-[10px] font-mono bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-1.5 py-0.5 text-gray-500 dark:text-gray-400">{t("commandPalette.esc")}</kbd>
        </div>
        <div className="max-h-[55vh] overflow-y-auto p-2">
          {items.length === 0 ? (
            <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-8">{t("commandPalette.noMatches")}</p>
          ) : (
            <>
              {renderGroup(t("commandPalette.groups.projects"), projectItems)}
              {renderGroup(t("commandPalette.groups.recentExecutions"), execItems)}
              {renderGroup(t("commandPalette.groups.testCases"), caseItems)}
              {renderGroup(t("commandPalette.groups.actions"), actionItems)}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
