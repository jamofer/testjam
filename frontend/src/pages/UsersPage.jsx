import { useEffect, useMemo, useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Activity, FolderKanban, Pencil, RotateCcw, Shield, Trash2, UserPlus, Users } from "lucide-react"
import { toast } from "sonner"

import { api } from "../api/client"
import { usersApi } from "../api/users"
import { AdminProjectsTab } from "../components/admin/AdminProjectsTab"
import { EditUserDialog } from "../components/admin/EditUserDialog"
import { UserActivityDialog } from "../components/admin/UserActivityDialog"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"

const groupsApi = {
  list: () => api.get("/groups").then(r => r.data),
  create: (data) => api.post("/groups", data).then(r => r.data),
  delete: (id) => api.delete(`/groups/${id}`),
}

export function UsersPage() {
  const queryClient = useQueryClient()
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [editTarget, setEditTarget] = useState(null)
  const [activityTarget, setActivityTarget] = useState(null)

  const { data: users = [] } = useQuery({
    queryKey: ["users", { includeDeleted }],
    queryFn: () => usersApi.list({ includeDeleted }),
  })
  const { data: groups = [] } = useQuery({ queryKey: ["groups"], queryFn: groupsApi.list })

  const restoreUser = useMutation({
    mutationFn: usersApi.restore,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["users"] }); toast.success("User restored") },
    onError: () => toast.error("Failed to restore user"),
  })

  const deleteGroup = useMutation({
    mutationFn: groupsApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["groups"] }); toast.success("Group deleted") },
  })

  const handleDeleted = () => {
    queryClient.invalidateQueries({ queryKey: ["users"] })
    setPendingDelete(null)
  }

  return (
    <div className="pl-14 pr-4 py-4 md:p-8 max-w-2xl xl:max-w-4xl 2xl:max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Admin</h1>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users"><Users size={13} className="mr-1" /> Users ({users.length})</TabsTrigger>
          <TabsTrigger value="groups"><Shield size={13} className="mr-1" /> Groups ({groups.length})</TabsTrigger>
          <TabsTrigger value="projects"><FolderKanban size={13} className="mr-1" /> Projects</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <div className="flex items-center justify-between mb-3">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input type="checkbox" checked={includeDeleted} onChange={e => setIncludeDeleted(e.target.checked)} />
              Show deleted
            </label>
            <CreateUserDialog />
          </div>
          <ul className="space-y-2">
            {users.map(user => (
              <UserRow
                key={user.id}
                user={user}
                onEdit={() => setEditTarget(user)}
                onActivity={() => setActivityTarget(user)}
                onDeleteRequest={() => setPendingDelete(user)}
                onRestore={() => restoreUser.mutate(user.id)}
              />
            ))}
          </ul>
        </TabsContent>

        <TabsContent value="groups">
          <div className="flex justify-end mb-3"><CreateGroupDialog /></div>
          <ul className="space-y-2">
            {groups.map(group => (
              <li key={group.id} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3 shadow-sm">
                <div>
                  <p className="font-medium text-gray-800">{group.name}</p>
                  <p className="text-xs text-gray-400">{group.members?.length ?? 0} members</p>
                </div>
                <Button size="icon" variant="ghost" onClick={() => deleteGroup.mutate(group.id)}>
                  <Trash2 size={14} />
                </Button>
              </li>
            ))}
          </ul>
        </TabsContent>

        <TabsContent value="projects">
          <AdminProjectsTab users={users} />
        </TabsContent>
      </Tabs>

      {pendingDelete && (
        <DeleteUserDialog
          user={pendingDelete}
          allUsers={users}
          onCancel={() => setPendingDelete(null)}
          onDeleted={handleDeleted}
        />
      )}
      {editTarget && (
        <EditUserDialog
          user={editTarget}
          open
          onOpenChange={(open) => { if (!open) setEditTarget(null) }}
        />
      )}
      {activityTarget && (
        <UserActivityDialog
          user={activityTarget}
          onClose={() => setActivityTarget(null)}
        />
      )}
    </div>
  )
}

function UserRow({ user, onEdit, onActivity, onDeleteRequest, onRestore }) {
  const isDeleted = !!user.deleted_at
  return (
    <li className="flex items-center justify-between bg-white border rounded-lg px-4 py-3 shadow-sm">
      <div>
        <p className="font-medium text-gray-800">
          {user.username}
          {user.is_admin && <Badge variant="outline" className="ml-2 text-[10px]">admin</Badge>}
        </p>
        <p className="text-xs text-gray-400">{user.email}</p>
      </div>
      <div className="flex items-center gap-2">
        {isDeleted ? (
          <>
            <Badge variant="secondary">DELETED</Badge>
            <Button size="sm" variant="outline" onClick={onRestore}>
              <RotateCcw size={12} /> Restore
            </Button>
          </>
        ) : (
          <>
            <Badge variant={user.is_active ? "success" : "secondary"}>
              {user.is_active ? "active" : "inactive"}
            </Badge>
            <Button size="icon" variant="ghost" title="Activity" onClick={onActivity}>
              <Activity size={14} />
            </Button>
            <Button size="icon" variant="ghost" title="Edit" onClick={onEdit}>
              <Pencil size={14} />
            </Button>
            <Button size="icon" variant="ghost" title="Delete" onClick={onDeleteRequest}>
              <Trash2 size={14} />
            </Button>
          </>
        )}
      </div>
    </li>
  )
}

function DeleteUserDialog({ user, allUsers, onCancel, onDeleted }) {
  const [unresolved, setUnresolved] = useState(null)
  const [actions, setActions] = useState({})

  const candidates = useMemo(
    () => Object.fromEntries(allUsers.map(u => [u.id, u.username])),
    [allUsers],
  )

  const deleteMutation = useMutation({
    mutationFn: (body) => usersApi.delete(user.id, body),
    onSuccess: () => {
      toast.success("User deleted")
      onDeleted()
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      if (error?.response?.status === 409 && detail?.owned_projects) {
        setUnresolved(detail.owned_projects)
        setActions(initialActions(detail.owned_projects))
      } else {
        toast.error("Failed to delete user")
        onCancel()
      }
    },
  })

  useEffect(() => {
    deleteMutation.mutate({})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id])

  if (unresolved === null) {
    return null
  }

  const submit = () => {
    const owned_projects = Object.entries(actions).map(([projectId, spec]) => ({
      project_id: Number(projectId),
      action: spec.action,
      new_owner_id: spec.action === "reassign" ? spec.new_owner_id : null,
    }))
    deleteMutation.mutate({ owned_projects })
  }

  const allResolved = Object.values(actions).every(
    spec => spec.action === "archive" || (spec.action === "reassign" && spec.new_owner_id),
  )

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onCancel() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete user "{user.username}"</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-600">
          This user uniquely owns the projects below. Choose what to do with each one.
        </p>
        <div className="space-y-3">
          {unresolved.map(project => (
            <ProjectActionRow
              key={project.project_id}
              project={project}
              candidates={candidates}
              spec={actions[project.project_id]}
              onChange={(spec) => setActions(prev => ({ ...prev, [project.project_id]: spec }))}
            />
          ))}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onCancel}>Cancel</Button>
          <Button onClick={submit} disabled={!allResolved || deleteMutation.isPending}>
            Delete user
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function ProjectActionRow({ project, candidates, spec, onChange }) {
  const validCandidates = project.candidate_member_ids.filter(id => candidates[id])
  return (
    <div className="border rounded-md p-3 space-y-2">
      <p className="font-medium text-sm text-gray-800">{project.project_name}</p>
      <div className="flex items-center gap-3 text-sm">
        <label className="flex items-center gap-1">
          <input
            type="radio"
            checked={spec.action === "reassign"}
            onChange={() => onChange({ action: "reassign", new_owner_id: spec.new_owner_id ?? validCandidates[0] ?? null })}
            disabled={validCandidates.length === 0}
          />
          Reassign to
        </label>
        <select
          className="text-sm border rounded px-2 py-1"
          disabled={spec.action !== "reassign" || validCandidates.length === 0}
          value={spec.new_owner_id ?? ""}
          onChange={e => onChange({ action: "reassign", new_owner_id: Number(e.target.value) })}
        >
          {validCandidates.length === 0 && <option value="">No candidates</option>}
          {validCandidates.map(id => (
            <option key={id} value={id}>{candidates[id]}</option>
          ))}
        </select>
        <label className="flex items-center gap-1">
          <input
            type="radio"
            checked={spec.action === "archive"}
            onChange={() => onChange({ action: "archive" })}
          />
          Archive project
        </label>
      </div>
    </div>
  )
}

function initialActions(projects) {
  const map = {}
  for (const project of projects) {
    const firstCandidate = project.candidate_member_ids[0] ?? null
    map[project.project_id] = firstCandidate
      ? { action: "reassign", new_owner_id: firstCandidate }
      : { action: "archive" }
  }
  return map
}

function CreateUserDialog() {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ username: "", email: "", password: "", full_name: "" })
  const queryClient = useQueryClient()

  const create = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.success("User created")
      setOpen(false)
      setForm({ username: "", email: "", password: "", full_name: "" })
    },
    onError: () => toast.error("Failed to create user"),
  })

  const field = (key) => ({ value: form[key], onChange: e => setForm(f => ({ ...f, [key]: e.target.value })) })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><UserPlus size={14} /> New user</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Create user</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>Username *</Label><Input {...field("username")} /></div>
          <div className="space-y-1"><Label>Email *</Label><Input type="email" {...field("email")} /></div>
          <div className="space-y-1"><Label>Full name</Label><Input {...field("full_name")} /></div>
          <div className="space-y-1"><Label>Password *</Label><Input type="password" {...field("password")} /></div>
          <Button className="w-full" onClick={() => create.mutate(form)} disabled={create.isPending}>
            Create
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function CreateGroupDialog() {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const queryClient = useQueryClient()

  const create = useMutation({
    mutationFn: groupsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] })
      toast.success("Group created")
      setOpen(false)
      setName("")
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline"><Shield size={14} /> New group</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Create group</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>Name *</Label>
            <Input value={name} onChange={e => setName(e.target.value)} /></div>
          <Button className="w-full" onClick={() => create.mutate({ name })} disabled={!name.trim()}>
            Create
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
