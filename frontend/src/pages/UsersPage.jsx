import { useEffect, useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Activity, FolderKanban, Pencil, RotateCcw, Shield, Trash2, UserPlus, Users } from "lucide-react"
import { toast } from "sonner"

import { groupsApi } from "../api/groups"
import { usersApi } from "../api/users"
import { AdminProjectsTab } from "../components/admin/AdminProjectsTab"
import { EditUserDialog } from "../components/admin/EditUserDialog"
import { GroupEditDialog } from "../components/admin/GroupEditDialog"
import { UserActivityDialog } from "../components/admin/UserActivityDialog"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"

export function UsersPage() {
  const { t } = useTranslation("admin")
  const queryClient = useQueryClient()
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [editTarget, setEditTarget] = useState(null)
  const [activityTarget, setActivityTarget] = useState(null)
  const [groupTarget, setGroupTarget] = useState(null)

  const { data: users = [] } = useQuery({
    queryKey: ["users", { includeDeleted }],
    queryFn: () => usersApi.list({ includeDeleted }),
  })
  const { data: groups = [] } = useQuery({ queryKey: ["groups"], queryFn: groupsApi.list })

  const restoreUser = useMutation({
    mutationFn: usersApi.restore,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["users"] }); toast.success(t("users.restored")) },
    onError: () => toast.error(t("users.restoreFailed")),
  })

  const deleteGroup = useMutation({
    mutationFn: groupsApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["groups"] }); toast.success(t("groups.deleted")) },
  })

  const handleDeleted = () => {
    queryClient.invalidateQueries({ queryKey: ["users"] })
    setPendingDelete(null)
  }

  return (
    <div className="pl-14 pr-4 py-4 md:p-8 max-w-2xl xl:max-w-4xl 2xl:max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users"><Users size={13} className="mr-1" /> {t("tabs.users", { count: users.length })}</TabsTrigger>
          <TabsTrigger value="groups"><Shield size={13} className="mr-1" /> {t("tabs.groups", { count: groups.length })}</TabsTrigger>
          <TabsTrigger value="projects"><FolderKanban size={13} className="mr-1" /> {t("tabs.projects")}</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <div className="flex items-center justify-between mb-3">
            <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <input type="checkbox" checked={includeDeleted} onChange={event => setIncludeDeleted(event.target.checked)} />
              {t("users.showDeleted")}
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
              <li key={group.id} className="flex items-center justify-between bg-white dark:bg-gray-900 border rounded-lg px-4 py-3 shadow-sm">
                <div className="min-w-0">
                  <p className="font-medium text-gray-800 dark:text-gray-100">{group.name}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                    {group.description ?? t("groups.row.noDescription")} · {t("groups.row.members", { count: group.members?.length ?? 0 })}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Button size="icon" variant="ghost" title={t("groups.row.edit")} onClick={() => setGroupTarget(group)}>
                    <Pencil size={14} />
                  </Button>
                  <Button size="icon" variant="ghost" title={t("groups.row.delete")} onClick={() => deleteGroup.mutate(group.id)}>
                    <Trash2 size={14} />
                  </Button>
                </div>
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
      {groupTarget && (
        <GroupEditDialog
          group={groupTarget}
          onClose={() => setGroupTarget(null)}
        />
      )}
    </div>
  )
}

function UserRow({ user, onEdit, onActivity, onDeleteRequest, onRestore }) {
  const { t } = useTranslation("admin")
  const isDeleted = !!user.deleted_at
  return (
    <li className="flex items-center justify-between bg-white dark:bg-gray-900 border rounded-lg px-4 py-3 shadow-sm">
      <div>
        <div className="font-medium text-gray-800 dark:text-gray-100 flex items-center gap-2">
          <span>{user.username}</span>
          {user.is_admin && <Badge variant="outline" className="text-[10px]">{t("users.row.admin")}</Badge>}
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500">{user.email}</p>
      </div>
      <div className="flex items-center gap-2">
        {isDeleted ? (
          <>
            <Badge variant="secondary">{t("users.row.deletedBadge")}</Badge>
            <Button size="sm" variant="outline" onClick={onRestore}>
              <RotateCcw size={12} /> {t("users.row.restore")}
            </Button>
          </>
        ) : (
          <>
            <Badge variant={user.is_active ? "success" : "secondary"}>
              {user.is_active ? t("users.row.active") : t("users.row.inactive")}
            </Badge>
            <Button size="icon" variant="ghost" title={t("users.row.activityTitle")} onClick={onActivity}>
              <Activity size={14} />
            </Button>
            <Button size="icon" variant="ghost" title={t("users.row.editTitle")} onClick={onEdit}>
              <Pencil size={14} />
            </Button>
            <Button size="icon" variant="ghost" title={t("users.row.deleteTitle")} onClick={onDeleteRequest}>
              <Trash2 size={14} />
            </Button>
          </>
        )}
      </div>
    </li>
  )
}

function DeleteUserDialog({ user, allUsers, onCancel, onDeleted }) {
  const { t } = useTranslation("admin")
  const [unresolved, setUnresolved] = useState(null)
  const [actions, setActions] = useState({})

  const candidates = useMemo(
    () => Object.fromEntries(allUsers.map(item => [item.id, item.username])),
    [allUsers],
  )

  const deleteMutation = useMutation({
    mutationFn: (body) => usersApi.delete(user.id, body),
    onSuccess: () => {
      toast.success(t("users.deleted"))
      onDeleted()
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      if (error?.response?.status === 409 && detail?.owned_projects) {
        setUnresolved(detail.owned_projects)
        setActions(initialActions(detail.owned_projects))
      } else {
        toast.error(t("users.deleteFailed"))
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
          <DialogTitle>{t("users.deleteDialog.title", { username: user.username })}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-600 dark:text-gray-300">{t("users.deleteDialog.intro")}</p>
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
          <Button variant="ghost" onClick={onCancel}>{t("users.deleteDialog.cancel")}</Button>
          <Button onClick={submit} disabled={!allResolved || deleteMutation.isPending}>
            {t("users.deleteDialog.confirm")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function ProjectActionRow({ project, candidates, spec, onChange }) {
  const { t } = useTranslation("admin")
  const validCandidates = project.candidate_member_ids.filter(id => candidates[id])
  return (
    <div className="border rounded-md p-3 space-y-2">
      <p className="font-medium text-sm text-gray-800 dark:text-gray-100">{project.project_name}</p>
      <div className="flex items-center gap-3 text-sm">
        <label className="flex items-center gap-1">
          <input
            type="radio"
            checked={spec.action === "reassign"}
            onChange={() => onChange({ action: "reassign", new_owner_id: spec.new_owner_id ?? validCandidates[0] ?? null })}
            disabled={validCandidates.length === 0}
          />
          {t("users.deleteDialog.reassign")}
        </label>
        <select
          className="text-sm border rounded px-2 py-1"
          disabled={spec.action !== "reassign" || validCandidates.length === 0}
          value={spec.new_owner_id ?? ""}
          onChange={event => onChange({ action: "reassign", new_owner_id: Number(event.target.value) })}
        >
          {validCandidates.length === 0 && <option value="">{t("users.deleteDialog.noCandidates")}</option>}
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
          {t("users.deleteDialog.archiveProject")}
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
  const { t } = useTranslation("admin")
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ username: "", email: "", password: "", full_name: "" })
  const queryClient = useQueryClient()

  const create = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.success(t("users.created"))
      setOpen(false)
      setForm({ username: "", email: "", password: "", full_name: "" })
    },
    onError: () => toast.error(t("users.createFailed")),
  })

  const field = (key) => ({ value: form[key], onChange: event => setForm(prev => ({ ...prev, [key]: event.target.value })) })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><UserPlus size={14} /> {t("users.newUser")}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>{t("users.createTitle")}</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>{t("users.fields.username")}</Label><Input {...field("username")} /></div>
          <div className="space-y-1"><Label>{t("users.fields.email")}</Label><Input type="email" {...field("email")} /></div>
          <div className="space-y-1"><Label>{t("users.fields.fullName")}</Label><Input {...field("full_name")} /></div>
          <div className="space-y-1"><Label>{t("users.fields.password")}</Label><Input type="password" {...field("password")} /></div>
          <Button className="w-full" onClick={() => create.mutate(form)} disabled={create.isPending}>
            {t("users.create")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function CreateGroupDialog() {
  const { t } = useTranslation("admin")
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const queryClient = useQueryClient()

  const create = useMutation({
    mutationFn: groupsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] })
      toast.success(t("groups.created"))
      setOpen(false)
      setName("")
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline"><Shield size={14} /> {t("groups.newGroup")}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>{t("groups.createTitle")}</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>{t("groups.fields.name")}</Label>
            <Input value={name} onChange={event => setName(event.target.value)} /></div>
          <Button className="w-full" onClick={() => create.mutate({ name })} disabled={!name.trim()}>
            {t("groups.create")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
