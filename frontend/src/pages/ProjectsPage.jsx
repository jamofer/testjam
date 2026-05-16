import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Plus, Trash2, FolderOpen, Search, Archive, ArchiveRestore } from 'lucide-react'
import {
  useProjects,
  useCreateProject,
  useDeleteProject,
  useArchiveProject,
  useUnarchiveProject,
} from '../hooks/useProjects'
import { useDebounced } from '../hooks/useDebounced'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { SearchInput } from '../components/ui/search-input'
import { PageHeader, PageBody } from '../components/ui/page-header'
import { EmptyState } from '../components/ui/empty-state'
import { SkeletonList } from '../components/ui/skeleton'
import { DashboardPanel } from '../components/project/DashboardPanel'

export function ProjectsPage() {
  const { t } = useTranslation('projects')
  const [includeArchived, setIncludeArchived] = useState(false)
  const { data: projects = [], isLoading } = useProjects({ includeArchived })
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const archiveProject = useArchiveProject()
  const unarchiveProject = useUnarchiveProject()
  const [newName, setNewName] = useState('')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search, 150)

  const filteredProjects = useMemo(() => {
    if (!debouncedSearch.trim()) return projects
    const q = debouncedSearch.trim().toLowerCase()
    return projects.filter(project =>
      project.name.toLowerCase().includes(q) ||
      (project.description ?? '').toLowerCase().includes(q)
    )
  }, [projects, debouncedSearch])

  const handleCreate = async (event) => {
    event.preventDefault()
    if (!newName.trim()) return
    await createProject.mutateAsync({ name: newName.trim() })
    setNewName('')
  }

  return (
    <>
      <PageHeader>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-3">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t('title')}</h1>
          <div className="flex flex-wrap gap-2">
            <SearchInput value={search} onChange={setSearch}
              placeholder={t('searchPlaceholder')} className="flex-1 min-w-[180px]" />
            <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <input
                type="checkbox"
                checked={includeArchived}
                onChange={event => setIncludeArchived(event.target.checked)}
              />
              {t('showArchived')}
            </label>
            <form onSubmit={handleCreate} className="flex gap-2">
              <input
                className="border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300 w-48"
                placeholder={t('createName')}
                value={newName}
                onChange={event => setNewName(event.target.value)}
              />
              <Button type="submit" size="sm" loading={createProject.isPending}>
                <Plus size={14} /> {t('create')}
              </Button>
            </form>
          </div>
        </div>
      </PageHeader>

      <PageBody>
      <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
      {isLoading && <SkeletonList count={4} itemClassName="h-32" />}

      <ul className="space-y-3">
        {filteredProjects.map(project => (
          <li key={project.id} className="bg-white dark:bg-gray-900 border rounded-xl px-4 py-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Link to={`/projects/${project.id}`} className="font-semibold text-gray-800 dark:text-gray-100 hover:text-primary-600 transition-colors">
                    {project.name}
                  </Link>
                  {project.archived_at && <Badge variant="secondary">{t('archived')}</Badge>}
                </div>
                {project.description && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5 truncate">{project.description}</p>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {project.archived_at ? (
                  <button
                    onClick={() => unarchiveProject.mutate(project.id)}
                    className="text-gray-400 dark:text-gray-500 hover:text-emerald-600 transition-colors"
                    title={t('unarchive')}
                  >
                    <ArchiveRestore size={15} />
                  </button>
                ) : (
                  <button
                    onClick={() => archiveProject.mutate(project.id)}
                    className="text-gray-400 dark:text-gray-500 hover:text-amber-600 transition-colors"
                    title={t('archive')}
                  >
                    <Archive size={15} />
                  </button>
                )}
                <button
                  onClick={() => deleteProject.mutate(project.id)}
                  className="text-gray-300 dark:text-gray-600 hover:text-red-500 transition-colors"
                  title={t('delete')}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
            <DashboardPanel project={project} compact />
          </li>
        ))}
      </ul>
      {!isLoading && projects.length === 0 && (
        <EmptyState
          icon={FolderOpen}
          title={t('empty.title')}
          description={t('empty.description')}
        />
      )}
      {!isLoading && projects.length > 0 && filteredProjects.length === 0 && (
        <EmptyState
          icon={Search}
          title={t('noMatches.title')}
          description={t('noMatches.description', { query: debouncedSearch })}
          compact
        />
      )}
      </div>
      </PageBody>
    </>
  )
}
