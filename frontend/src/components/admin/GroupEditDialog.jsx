import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { groupsApi } from "../../api/groups"
import { usersApi } from "../../api/users"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"

export function GroupEditDialog({ group, onClose }) {
  const { t } = useTranslation("admin")
  const queryClient = useQueryClient()
  const [name, setName] = useState(group.name)
  const [description, setDescription] = useState(group.description ?? "")

  const { data: members = [] } = useQuery({
    queryKey: ["group-members", group.id],
    queryFn: () => groupsApi.listMembers(group.id),
  })
  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list(),
  })

  useEffect(() => {
    setName(group.name)
    setDescription(group.description ?? "")
  }, [group.id, group.name, group.description])

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["groups"] })
    queryClient.invalidateQueries({ queryKey: ["group-members", group.id] })
  }

  const update = useMutation({
    mutationFn: () => groupsApi.update(group.id, { name, description: description || null }),
    onSuccess: () => { invalidate(); toast.success(t("groups.edit.updated")) },
    onError: () => toast.error(t("groups.edit.updateFailed")),
  })
  const addMember = useMutation({
    mutationFn: (userId) => groupsApi.addMember(group.id, userId),
    onSuccess: invalidate,
    onError: (error) => toast.error(error?.response?.data?.detail ?? t("groups.edit.addMemberFailed")),
  })
  const removeMember = useMutation({
    mutationFn: (userId) => groupsApi.removeMember(group.id, userId),
    onSuccess: invalidate,
    onError: () => toast.error(t("groups.edit.removeMemberFailed")),
  })

  const memberIds = new Set(members.map(member => member.user_id))
  const candidates = users.filter(user => !memberIds.has(user.id) && !user.deleted_at)

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{t("groups.edit.title", { name: group.name })}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <Field label={t("groups.edit.name")}>
            <Input value={name} onChange={event => setName(event.target.value)} />
          </Field>
          <Field label={t("groups.edit.description")}>
            <Input
              value={description}
              onChange={event => setDescription(event.target.value)}
              placeholder={t("groups.edit.descriptionPlaceholder")}
            />
          </Field>
          <div className="flex justify-end">
            <Button size="sm" onClick={() => update.mutate()} disabled={update.isPending}>
              {t("groups.edit.saveDetails")}
            </Button>
          </div>
        </div>

        <div className="pt-4 mt-4 border-t space-y-2">
          <p className="font-medium text-gray-800 dark:text-gray-100">{t("groups.edit.membersCount", { count: members.length })}</p>
          <MemberList members={members} onRemove={(userId) => removeMember.mutate(userId)} />
          <AddMemberRow candidates={candidates} onAdd={(userId) => addMember.mutate(userId)} />
        </div>
      </DialogContent>
    </Dialog>
  )
}

function Field({ label, children }) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      {children}
    </div>
  )
}

function MemberList({ members, onRemove }) {
  const { t } = useTranslation("admin")
  if (!members.length) {
    return <p className="text-sm text-gray-400 dark:text-gray-500 py-2">{t("groups.edit.noMembers")}</p>
  }
  return (
    <ul className="divide-y border rounded-md max-h-60 overflow-y-auto">
      {members.map(member => (
        <li key={member.user_id} className="flex items-center justify-between px-3 py-2 text-sm">
          <span className="text-gray-800 dark:text-gray-100">{member.username}</span>
          <button
            onClick={() => onRemove(member.user_id)}
            className="text-gray-300 dark:text-gray-600 hover:text-red-500 transition-colors p-1"
            aria-label={t("groups.edit.removeAria", { username: member.username })}
          >
            <Trash2 size={13} />
          </button>
        </li>
      ))}
    </ul>
  )
}

function AddMemberRow({ candidates, onAdd }) {
  const { t } = useTranslation("admin")
  const [userId, setUserId] = useState("")

  if (!candidates.length) return null

  const submit = (event) => {
    event.preventDefault()
    if (!userId) return
    onAdd(Number(userId))
    setUserId("")
  }

  return (
    <form onSubmit={submit} className="flex gap-2 pt-2">
      <select
        value={userId}
        onChange={event => setUserId(event.target.value)}
        className="flex-1 text-sm border rounded-md px-2 py-1.5 bg-white dark:bg-gray-900"
      >
        <option value="">{t("groups.edit.selectUser")}</option>
        {candidates.map(user => (
          <option key={user.id} value={user.id}>{user.username}</option>
        ))}
      </select>
      <Button type="submit" size="sm">
        <Plus size={14} /> {t("groups.edit.addMember")}
      </Button>
    </form>
  )
}
