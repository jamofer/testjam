import { useState } from "react"
import { useParams } from "react-router-dom"
import { Shield, Trash2, Plus, Key, Copy, Eye, EyeOff, Clock } from "lucide-react"
import { useMembers, useAddMember, useUpdateMember, useRemoveMember } from "../hooks/useMembers"
import { useProjectTokens, useCreateProjectToken, useRevokeProjectToken } from "../hooks/useTokens"
import { useQuery } from "@tanstack/react-query"
import { api } from "../api/client"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { toast } from "sonner"

const ROLES = ["owner", "tester", "viewer"]

const ROLE_BADGE = {
  owner:  "bg-purple-100 text-purple-700",
  tester: "bg-blue-100 text-blue-700",
  viewer: "bg-gray-100 text-gray-600",
}

function fmtDate(iso) {
  if (!iso) return "Never"
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

function NewTokenValue({ token, onDone }) {
  const [visible, setVisible] = useState(false)
  const copy = () => { navigator.clipboard.writeText(token); toast.success("Token copied") }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
      <p className="text-sm font-medium text-green-800">Token created — copy it now, it won't be shown again.</p>
      <div className="flex items-center gap-2">
        <code className="flex-1 bg-white border rounded px-3 py-1.5 text-sm font-mono text-gray-800 truncate">
          {visible ? token : token.slice(0, 4) + "•".repeat(token.length - 4)}
        </code>
        <button onClick={() => setVisible(v => !v)} className="text-gray-400 hover:text-gray-700 p-1">
          {visible ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
        <button onClick={copy} className="text-gray-400 hover:text-gray-700 p-1">
          <Copy size={15} />
        </button>
      </div>
      <Button size="sm" variant="outline" onClick={onDone}>Done</Button>
    </div>
  )
}

function TokensSection({ projectId }) {
  const { data: tokens = [] } = useProjectTokens(projectId)
  const create = useCreateProjectToken(projectId)
  const revoke = useRevokeProjectToken(projectId)
  const [name, setName] = useState("")
  const [newToken, setNewToken] = useState(null)

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    try {
      const t = await create.mutateAsync({ name: name.trim() })
      setNewToken(t.token)
      setName("")
    } catch {
      toast.error("Failed to create token")
    }
  }

  const handleRevoke = async (tokenId) => {
    try {
      await revoke.mutateAsync(tokenId)
      toast.success("Token revoked")
    } catch {
      toast.error("Failed to revoke token")
    }
  }

  return (
    <section className="bg-white border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b flex items-center gap-2">
        <Key size={15} className="text-gray-500" />
        <h2 className="font-semibold text-gray-800">Project API Tokens</h2>
      </div>

      <div className="p-5 space-y-4">
        {newToken && <NewTokenValue token={newToken} onDone={() => setNewToken(null)} />}

        <form onSubmit={handleCreate} className="flex gap-2">
          <Input
            value={name} onChange={e => setName(e.target.value)}
            placeholder="Token name (e.g. CI pipeline)" className="flex-1" />
          <Button type="submit" size="sm" loading={create.isPending}><Plus size={14} /> New token</Button>
        </form>

        {tokens.length > 0 && (
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-400 uppercase">
              <tr>
                <th className="text-left pb-2">Name</th>
                <th className="text-left pb-2">Prefix</th>
                <th className="text-left pb-2">Last used</th>
                <th className="text-left pb-2">Created</th>
                <th />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {tokens.map(t => (
                <tr key={t.id}>
                  <td className="py-2 font-medium text-gray-800">{t.name}</td>
                  <td className="py-2 font-mono text-gray-500">{t.prefix}…</td>
                  <td className="py-2 text-gray-400 flex items-center gap-1">
                    <Clock size={11} />{fmtDate(t.last_used_at)}
                  </td>
                  <td className="py-2 text-gray-400">{fmtDate(t.created_at)}</td>
                  <td className="py-2 text-right">
                    <button onClick={() => handleRevoke(t.id)}
                      className="text-gray-300 hover:text-red-500 transition-colors p-1">
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {tokens.length === 0 && !newToken && (
          <p className="text-sm text-gray-400">No project tokens yet.</p>
        )}
      </div>
    </section>
  )
}

export function MembersPage() {
  const { id: projectId } = useParams()
  const { data: members = [], isLoading } = useMembers(projectId)
  const addMember = useAddMember(projectId)
  const updateMember = useUpdateMember(projectId)
  const removeMember = useRemoveMember(projectId)

  const { data: allUsers = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then(r => r.data),
  })

  const [selectedUserId, setSelectedUserId] = useState("")
  const [selectedRole, setSelectedRole] = useState("tester")

  const memberIds = new Set(members.map(m => m.user_id))
  const addableUsers = allUsers.filter(u => !memberIds.has(u.id))

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!selectedUserId) return
    try {
      await addMember.mutateAsync({ user_id: Number(selectedUserId), role: selectedRole })
      setSelectedUserId("")
      toast.success("Member added")
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? "Failed to add member")
    }
  }

  const handleRoleChange = async (userId, role) => {
    try {
      await updateMember.mutateAsync({ userId, data: { role } })
    } catch {
      toast.error("Failed to update role")
    }
  }

  const handleRemove = async (userId) => {
    try {
      await removeMember.mutateAsync(userId)
      toast.success("Member removed")
    } catch {
      toast.error("Failed to remove member")
    }
  }

  if (isLoading) return <p className="text-gray-500">Loading…</p>

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Members & Access</h1>

      {/* Members */}
      <section className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b flex items-center gap-2">
          <Shield size={15} className="text-gray-500" />
          <h2 className="font-semibold text-gray-800">Members</h2>
        </div>

        <div className="divide-y divide-gray-50">
          {members.map(m => (
            <div key={m.id} className="flex items-center gap-3 px-5 py-3">
              <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold shrink-0">
                {(m.full_name ?? m.username).split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{m.full_name ?? m.username}</p>
                <p className="text-xs text-gray-400">@{m.username}</p>
              </div>
              <select
                value={m.role}
                onChange={e => handleRoleChange(m.user_id, e.target.value)}
                className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer ${ROLE_BADGE[m.role]}`}
              >
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
              <button onClick={() => handleRemove(m.user_id)}
                className="text-gray-300 hover:text-red-500 transition-colors p-1 shrink-0">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {members.length === 0 && (
            <p className="px-5 py-4 text-sm text-gray-400">No members yet.</p>
          )}
        </div>

        {addableUsers.length > 0 && (
          <form onSubmit={handleAdd} className="px-5 py-4 border-t bg-gray-50 flex gap-2">
            <select
              value={selectedUserId}
              onChange={e => setSelectedUserId(e.target.value)}
              className="flex-1 text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
            >
              <option value="">Select user…</option>
              {addableUsers.map(u => (
                <option key={u.id} value={u.id}>{u.full_name ? `${u.full_name} (@${u.username})` : `@${u.username}`}</option>
              ))}
            </select>
            <select
              value={selectedRole}
              onChange={e => setSelectedRole(e.target.value)}
              className="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
            >
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <Button type="submit" size="sm" loading={addMember.isPending}>
              <Plus size={14} /> Add
            </Button>
          </form>
        )}
      </section>

      <TokensSection projectId={projectId} />
    </div>
  )
}
