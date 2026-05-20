import { useState } from "react"
import { useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Shield, Trash2, Plus } from "lucide-react"
import { useMembers, useAddMember, useUpdateMember, useRemoveMember } from "../hooks/useMembers"
import { useProject } from "../hooks/useProjects"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { useQuery } from "@tanstack/react-query"
import { api } from "../api/client"
import { Button } from "../components/ui/button"
import { EmptyState } from "../components/ui/empty-state"
import { ProjectGroupsSection } from "../components/project/ProjectGroupsSection"
import { toast } from "sonner"

const ROLES = ["owner", "tester", "viewer"]

const ROLE_BADGE = {
  owner:  "bg-purple-100 text-purple-700",
  tester: "bg-blue-100 text-blue-700",
  viewer: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300",
}

export function MembersPage() {
  const { t } = useTranslation(["members", "nav"])
  const { id: projectId } = useParams()
  const { data: members = [], isLoading } = useMembers(projectId)
  const { data: project } = useProject(projectId)
  const addMember = useAddMember(projectId)
  const updateMember = useUpdateMember(projectId)
  const removeMember = useRemoveMember(projectId)

  const { data: allUsers = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then(response => response.data),
  })

  const [selectedUserId, setSelectedUserId] = useState("")
  const [selectedRole, setSelectedRole] = useState("tester")

  const memberIds = new Set(members.map(member => member.user_id))
  const addableUsers = allUsers.filter(user => !memberIds.has(user.id))

  const handleAdd = async (event) => {
    event.preventDefault()
    if (!selectedUserId) return
    try {
      await addMember.mutateAsync({ user_id: Number(selectedUserId), role: selectedRole })
      setSelectedUserId("")
      toast.success(t("member.added"))
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("member.addFailed"))
    }
  }

  const handleRoleChange = async (userId, role) => {
    try {
      await updateMember.mutateAsync({ userId, data: { role } })
    } catch {
      toast.error(t("member.roleFailed"))
    }
  }

  const handleRemove = async (userId) => {
    try {
      await removeMember.mutateAsync(userId)
      toast.success(t("member.removed"))
    } catch {
      toast.error(t("member.removeFailed"))
    }
  }

  if (isLoading) return <p className="text-gray-500 dark:text-gray-400">{t("loading")}</p>

  return (
    <div className="pl-14 pr-4 py-4 md:p-8 max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
      <Breadcrumbs
        crumbs={[
          { label: t("nav:global.projects"), to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${projectId}` },
          { label: t("nav:project.members") },
        ]}
      />
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>

      <section className="bg-white dark:bg-gray-900 border rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b flex items-center gap-2">
          <Shield size={15} className="text-gray-500 dark:text-gray-400" />
          <h2 className="font-semibold text-gray-800 dark:text-gray-100">{t("members")}</h2>
        </div>

        <div className="divide-y divide-gray-50">
          {members.map(member => (
            <div key={member.id} className="flex items-center gap-3 px-5 py-3">
              <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold shrink-0">
                {(member.full_name ?? member.username).split(" ").map(word => word[0]).join("").slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{member.full_name ?? member.username}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">@{member.username}</p>
              </div>
              <select
                value={member.role}
                onChange={event => handleRoleChange(member.user_id, event.target.value)}
                className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer ${ROLE_BADGE[member.role]}`}
              >
                {ROLES.map(role => <option key={role} value={role}>{t(`roles.${role}`)}</option>)}
              </select>
              <button onClick={() => handleRemove(member.user_id)}
                aria-label={t("member.removeAria")}
                className="text-gray-300 dark:text-gray-600 hover:text-red-500 transition-colors p-1 shrink-0">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {members.length === 0 && (
            <div className="px-5 py-4">
              <EmptyState
                icon={Shield}
                title={t("membersEmpty.title")}
                description={t("membersEmpty.description")}
                compact
              />
            </div>
          )}
        </div>

        {addableUsers.length > 0 && (
          <form onSubmit={handleAdd} className="px-5 py-4 border-t bg-gray-50 dark:bg-gray-900 flex gap-2">
            <select
              value={selectedUserId}
              onChange={event => setSelectedUserId(event.target.value)}
              className="flex-1 text-sm border border-gray-200 dark:border-gray-700 rounded-md px-3 py-1.5 bg-white dark:bg-gray-900 focus:outline-none focus:ring-1 focus:ring-primary-400"
            >
              <option value="">{t("member.selectUser")}</option>
              {addableUsers.map(user => (
                <option key={user.id} value={user.id}>{user.full_name ? `${user.full_name} (@${user.username})` : `@${user.username}`}</option>
              ))}
            </select>
            <select
              value={selectedRole}
              onChange={event => setSelectedRole(event.target.value)}
              className="text-sm border border-gray-200 dark:border-gray-700 rounded-md px-3 py-1.5 bg-white dark:bg-gray-900 focus:outline-none focus:ring-1 focus:ring-primary-400"
            >
              {ROLES.map(role => <option key={role} value={role}>{t(`roles.${role}`)}</option>)}
            </select>
            <Button type="submit" size="sm" loading={addMember.isPending}>
              <Plus size={14} /> {t("member.add")}
            </Button>
          </form>
        )}
      </section>

      <ProjectGroupsSection projectId={projectId} />
    </div>
  )
}
