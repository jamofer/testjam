import { useState } from "react"
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
    onError: () => toast.error("Failed to update archive state"),
  })

  if (isPending) return <SkeletonList count={4} />
  if (!projects.length) return <p className="text-gray-500 text-sm">No projects.</p>

  return (
    <>
      <div className="overflow-x-auto border rounded-lg bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-3 py-2">Project</th>
              <th className="px-3 py-2">Owner</th>
              <th className="px-3 py-2 text-right">Members</th>
              <th className="px-3 py-2 text-right">Cases</th>
              <th className="px-3 py-2">Last execution</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2 text-right">Actions</th>
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
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-3 py-2 font-medium text-gray-800">{project.name}</td>
      <td className="px-3 py-2 text-gray-600">{project.owner_username ?? "—"}</td>
      <td className="px-3 py-2 text-right text-gray-600">{project.member_count}</td>
      <td className="px-3 py-2 text-right text-gray-600">{project.case_count}</td>
      <td className="px-3 py-2 text-gray-600">
        {project.last_execution_at ? <DateLabel iso={project.last_execution_at} /> : "—"}
      </td>
      <td className="px-3 py-2">
        {project.archived_at
          ? <Badge variant="secondary">archived</Badge>
          : <Badge variant="success">active</Badge>}
      </td>
      <td className="px-3 py-2">
        <div className="flex justify-end gap-1">
          <IconAction title="Transfer ownership" onClick={onTransfer}><UserCog size={14} /></IconAction>
          <IconAction
            title={project.archived_at ? "Unarchive" : "Archive"}
            onClick={onArchive}
          >
            {project.archived_at ? <ArchiveRestore size={14} /> : <Archive size={14} />}
          </IconAction>
          <IconAction
            title="Export"
            onClick={() => projectsApi.exportZip(project.id)}
          ><Download size={14} /></IconAction>
          <IconAction title="Delete" onClick={onDelete}><Trash2 size={14} /></IconAction>
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
