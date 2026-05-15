import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "../../api/client"
import { Plus, Trash2, Users } from "lucide-react"
import { toast } from "sonner"

import { projectGroupsApi } from "../../api/projectGroups"
import { Button } from "../ui/button"
import { EmptyState } from "../ui/empty-state"

const ROLES = ["owner", "tester", "viewer"]
const ROLE_BADGE = {
  owner: "bg-purple-100 text-purple-700",
  tester: "bg-blue-100 text-blue-700",
  viewer: "bg-gray-100 text-gray-600",
}

export function ProjectGroupsSection({ projectId }) {
  const queryClient = useQueryClient()
  const queryKey = ["project-groups", projectId]

  const { data: assignments = [] } = useQuery({
    queryKey,
    queryFn: () => projectGroupsApi.list(projectId),
  })
  const { data: groups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.get("/groups").then(r => r.data),
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey })

  const add = useMutation({
    mutationFn: ({ groupId, role }) => projectGroupsApi.add(projectId, groupId, role),
    onSuccess: () => { invalidate(); toast.success("Group assigned") },
    onError: (error) => toast.error(error?.response?.data?.detail ?? "Failed to assign group"),
  })
  const update = useMutation({
    mutationFn: ({ groupId, role }) => projectGroupsApi.update(projectId, groupId, role),
    onSuccess: invalidate,
    onError: () => toast.error("Failed to update role"),
  })
  const remove = useMutation({
    mutationFn: (groupId) => projectGroupsApi.remove(projectId, groupId),
    onSuccess: () => { invalidate(); toast.success("Group removed") },
    onError: () => toast.error("Failed to remove group"),
  })

  const assignedIds = new Set(assignments.map(assignment => assignment.group_id))
  const candidates = groups.filter(group => !assignedIds.has(group.id))

  return (
    <section className="bg-white border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b flex items-center gap-2">
        <Users size={15} className="text-gray-500" />
        <h2 className="font-semibold text-gray-800">Group access</h2>
      </div>

      <div className="divide-y divide-gray-50">
        {assignments.map(assignment => (
          <AssignmentRow
            key={assignment.id}
            assignment={assignment}
            onRoleChange={(role) => update.mutate({ groupId: assignment.group_id, role })}
            onRemove={() => remove.mutate(assignment.group_id)}
          />
        ))}
        {assignments.length === 0 && (
          <div className="px-5 py-4">
            <EmptyState
              icon={Users}
              title="No groups assigned"
              description="Assign a group to give every member of it the same role on this project."
              compact
            />
          </div>
        )}
      </div>

      {candidates.length > 0 && (
        <AddRow candidates={candidates} onSubmit={(groupId, role) => add.mutate({ groupId, role })} />
      )}
    </section>
  )
}

function AssignmentRow({ assignment, onRoleChange, onRemove }) {
  return (
    <div className="flex items-center gap-3 px-5 py-3">
      <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center shrink-0">
        <Users size={14} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">{assignment.group_name}</p>
        <p className="text-xs text-gray-400">{assignment.member_count} member{assignment.member_count === 1 ? "" : "s"}</p>
      </div>
      <select
        value={assignment.role}
        onChange={(event) => onRoleChange(event.target.value)}
        className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer ${ROLE_BADGE[assignment.role]}`}
      >
        {ROLES.map(role => <option key={role} value={role}>{role}</option>)}
      </select>
      <button
        onClick={onRemove}
        className="text-gray-300 hover:text-red-500 transition-colors p-1 shrink-0"
        aria-label="Remove group"
      >
        <Trash2 size={14} />
      </button>
    </div>
  )
}

function AddRow({ candidates, onSubmit }) {
  const [groupId, setGroupId] = useState("")
  const [role, setRole] = useState("tester")

  const submit = (event) => {
    event.preventDefault()
    if (!groupId) return
    onSubmit(Number(groupId), role)
    setGroupId("")
  }

  return (
    <form onSubmit={submit} className="px-5 py-4 border-t bg-gray-50 flex gap-2">
      <select
        value={groupId}
        onChange={(event) => setGroupId(event.target.value)}
        className="flex-1 text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
      >
        <option value="">Select group…</option>
        {candidates.map(group => (
          <option key={group.id} value={group.id}>{group.name}</option>
        ))}
      </select>
      <select
        value={role}
        onChange={(event) => setRole(event.target.value)}
        className="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
      >
        {ROLES.map(option => <option key={option} value={option}>{option}</option>)}
      </select>
      <Button type="submit" size="sm">
        <Plus size={14} /> Assign
      </Button>
    </form>
  )
}
