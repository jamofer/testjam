import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Archive, ArchiveRestore, Download, Trash2, UserCog } from "lucide-react"
import { toast } from "sonner"

import { adminApi } from "../../api/admin"
import { projectsApi } from "../../api/projects"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { DateLabel } from "../ui/date-label"
import { SkeletonList } from "../ui/skeleton"
import { TransferOwnershipDialog } from "./TransferOwnershipDialog"
import { DeleteProjectDialog } from "./DeleteProjectDialog"

export function AdminProjectsTab({ users }) {
  const { t } = useTranslation("admin")
  const queryClient = useQueryClient()
  const [transferProject, setTransferProject] = useState(null)
  const [deleteProject, setDeleteProject] = useState(null)

  const { data: projects, isPending } = useQuery({
    queryKey: ["admin-projects"],
    queryFn: () => adminApi.listProjects(),
  })

  const archive = useMutation({
    mutationFn: (project) =>
      project.archived_at ? projectsApi.unarchive(project.id) : projectsApi.archive(project.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] })
    },
    onError: () => toast.error(t("projects.archiveFailed")),
  })

  if (isPending) return <SkeletonList count={4} />
  if (!projects.length) return <p className="text-gray-500 dark:text-gray-400 text-sm">{t("projects.empty")}</p>

  return (
    <>
      <div className="overflow-x-auto border rounded-lg bg-white dark:bg-gray-900">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900 text-left text-xs uppercase text-gray-500 dark:text-gray-400">
            <tr>
              <th className="px-3 py-2">{t("projects.headers.project")}</th>
              <th className="px-3 py-2">{t("projects.headers.owner")}</th>
              <th className="px-3 py-2 text-right">{t("projects.headers.members")}</th>
              <th className="px-3 py-2 text-right">{t("projects.headers.cases")}</th>
              <th className="px-3 py-2">{t("projects.headers.lastExecution")}</th>
              <th className="px-3 py-2">{t("projects.headers.status")}</th>
              <th className="px-3 py-2 text-right">{t("projects.headers.actions")}</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {projects.map((project) => (
              <ProjectRow
                key={project.id}
                project={project}
                onTransfer={() => setTransferProject(project)}
                onArchive={() => archive.mutate(project)}
                onDelete={() => setDeleteProject(project)}
              />
            ))}
          </tbody>
        </table>
      </div>
      {transferProject && (
        <TransferOwnershipDialog
          project={transferProject}
          users={users}
          onClose={() => setTransferProject(null)}
        />
      )}
      {deleteProject && (
        <DeleteProjectDialog
          project={deleteProject}
          onClose={() => setDeleteProject(null)}
        />
      )}
    </>
  )
}

function ProjectRow({ project, onTransfer, onArchive, onDelete }) {
  const { t } = useTranslation("admin")
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">
      <td className="px-3 py-2 font-medium text-gray-800 dark:text-gray-100">{project.name}</td>
      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">{project.owner_username ?? "—"}</td>
      <td className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">{project.member_count}</td>
      <td className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">{project.case_count}</td>
      <td className="px-3 py-2 text-gray-600 dark:text-gray-300">
        {project.last_execution_at ? <DateLabel iso={project.last_execution_at} /> : "—"}
      </td>
      <td className="px-3 py-2">
        {project.archived_at
          ? <Badge variant="secondary">{t("projects.statuses.archived")}</Badge>
          : <Badge variant="success">{t("projects.statuses.active")}</Badge>}
      </td>
      <td className="px-3 py-2">
        <div className="flex justify-end gap-1">
          <IconAction title={t("projects.actions.transfer")} onClick={onTransfer}><UserCog size={14} /></IconAction>
          <IconAction
            title={project.archived_at ? t("projects.actions.unarchive") : t("projects.actions.archive")}
            onClick={onArchive}
          >
            {project.archived_at ? <ArchiveRestore size={14} /> : <Archive size={14} />}
          </IconAction>
          <IconAction
            title={t("projects.actions.export")}
            onClick={() => projectsApi.exportZip(project.id)}
          ><Download size={14} /></IconAction>
          <IconAction title={t("projects.actions.delete")} onClick={onDelete}><Trash2 size={14} /></IconAction>
        </div>
      </td>
    </tr>
  )
}

function IconAction({ title, onClick, children }) {
  return (
    <Button size="icon" variant="ghost" title={title} onClick={onClick}>
      {children}
    </Button>
  )
}
