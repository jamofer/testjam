import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Trash2, FolderOpen, PlayCircle, Search } from 'lucide-react'
import { useProjects, useCreateProject, useDeleteProject } from '../hooks/useProjects'
import { useDebounced } from '../hooks/useDebounced'
import { Button } from '../components/ui/button'
import { SearchInput } from '../components/ui/search-input'
import { EmptyState } from '../components/ui/empty-state'
import { SkeletonList } from '../components/ui/skeleton'

function formatDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export function ProjectsPage() {
  const { data: projects = [], isLoading } = useProjects()
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const [newName, setNewName] = useState('')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search, 150)

  const filteredProjects = useMemo(() => {
    if (!debouncedSearch.trim()) return projects
    const q = debouncedSearch.trim().toLowerCase()
    return projects.filter(p =>
      p.name.toLowerCase().includes(q) ||
      (p.description ?? '').toLowerCase().includes(q)
    )
  }, [projects, debouncedSearch])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newName.trim()) return
    await createProject.mutateAsync({ name: newName.trim() })
    setNewName('')
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Projects</h1>

      {isLoading && <SkeletonList count={4} itemClassName="h-20" />}

      <form onSubmit={handleCreate} className="flex gap-2 mb-6">
        <input
          className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
          placeholder="New project name…"
          value={newName}
          onChange={e => setNewName(e.target.value)}
        />
        <Button type="submit" size="sm" loading={createProject.isPending}>
          <Plus size={14} /> Create
        </Button>
      </form>

      <ul className="space-y-3">
        {filteredProjects.map(p => (
          <li key={p.id} className="bg-white border rounded-xl px-4 py-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <Link to={`/projects/${p.id}`} className="font-semibold text-gray-800 hover:text-primary-600 transition-colors">
                  {p.name}
                </Link>
                {p.description && (
                  <p className="text-sm text-gray-500 mt-0.5 truncate">{p.description}</p>
                )}
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span className="flex items-center gap-1">
                    <FolderOpen size={12} />
                    {p.suite_count} {p.suite_count === 1 ? 'suite' : 'suites'} · {p.case_count} {p.case_count === 1 ? 'case' : 'cases'}
                  </span>
                  <span className="flex items-center gap-1">
                    <PlayCircle size={12} />
                    {p.execution_count} {p.execution_count === 1 ? 'execution' : 'executions'}
                    {p.last_execution_at && ` · last ${formatDate(p.last_execution_at)}`}
                  </span>
                </div>
              </div>
              <button
                onClick={() => deleteProject.mutate(p.id)}
                className="text-gray-300 hover:text-red-500 transition-colors mt-0.5 shrink-0"
                title="Delete project"
              >
                <Trash2 size={15} />
              </button>
            </div>
          </li>
        ))}
      </ul>
      {!isLoading && projects.length === 0 && (
        <EmptyState
          icon={FolderOpen}
          title="No projects yet"
          description="Projects group your test suites, cases and executions. Create one above to get started."
        />
      )}
      {!isLoading && projects.length > 0 && filteredProjects.length === 0 && (
        <EmptyState
          icon={Search}
          title="No matches"
          description={`No projects match "${debouncedSearch}". Try a different search.`}
          compact
        />
      )}
    </div>
  )
}
