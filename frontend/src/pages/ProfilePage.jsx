import { useState, useEffect } from "react"
import { useMe, useUpdateMe, useChangePassword } from "../hooks/useAuth"
import { useUserTokens, useCreateUserToken, useRevokeUserToken } from "../hooks/useTokens"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { EmptyState } from "../components/ui/empty-state"
import { Trash2, Plus, Key, Copy, Eye, EyeOff, Clock } from "lucide-react"
import { toast } from "sonner"

function fmtDate(iso) {
  if (!iso) return "Never"
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

function NewTokenBanner({ token, onDone }) {
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
        <button onClick={copy} className="text-gray-400 hover:text-gray-700 p-1"><Copy size={15} /></button>
      </div>
      <Button size="sm" variant="outline" onClick={onDone}>Done</Button>
    </div>
  )
}

function UserTokensSection() {
  const { data: tokens = [] } = useUserTokens()
  const create = useCreateUserToken()
  const revoke = useRevokeUserToken()
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

  const handleRevoke = async (id) => {
    try {
      await revoke.mutateAsync(id)
      toast.success("Token revoked")
    } catch {
      toast.error("Failed to revoke token")
    }
  }

  return (
    <div className="bg-white border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Key size={15} className="text-gray-500" />
        <h2 className="font-semibold text-gray-700">API Tokens</h2>
      </div>

      {newToken && <NewTokenBanner token={newToken} onDone={() => setNewToken(null)} />}

      <form onSubmit={handleCreate} className="flex gap-2">
        <Input value={name} onChange={e => setName(e.target.value)} placeholder="Token name" className="flex-1" />
        <Button type="submit" size="sm" loading={create.isPending}><Plus size={14} /> New token</Button>
      </form>

      {tokens.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-400 uppercase">
            <tr>
              <th className="text-left pb-2">Name</th>
              <th className="text-left pb-2">Prefix</th>
              <th className="text-left pb-2">Last used</th>
              <th />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {tokens.map(t => (
              <tr key={t.id}>
                <td className="py-2 font-medium text-gray-800">{t.name}</td>
                <td className="py-2 font-mono text-gray-500">{t.prefix}…</td>
                <td className="py-2 text-gray-400 flex items-center gap-1"><Clock size={11} />{fmtDate(t.last_used_at)}</td>
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
        <EmptyState
          icon={Key}
          title="No personal tokens"
          description="Create one to authenticate from CI scripts or the listener."
          compact
        />
      )}
    </div>
  )
}

export function ProfilePage() {
  const { data: user } = useMe()
  const updateMe = useUpdateMe()
  const changePassword = useChangePassword()

  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  useEffect(() => {
    if (user) {
      setFullName(user.full_name ?? "")
      setEmail(user.email ?? "")
    }
  }, [user])

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    await updateMe.mutateAsync({ full_name: fullName || null, email })
    toast.success("Profile updated")
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) return toast.error("Passwords don't match")
    if (newPassword.length < 8) return toast.error("Password must be at least 8 characters")
    try {
      await changePassword.mutateAsync({ current_password: currentPassword, new_password: newPassword })
      toast.success("Password changed")
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? "Failed to change password")
    }
  }

  if (!user) return null

  const initials = (user.full_name ?? user.username)
    .split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()

  return (
    <div className="pl-14 pr-4 py-4 md:p-8 max-w-lg space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Profile</h1>
        <p className="text-sm text-gray-500 mt-0.5">Manage your account settings</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-2xl font-bold">
          {initials}
        </div>
        <div>
          <p className="font-semibold text-gray-800 text-lg">{user.full_name || user.username}</p>
          <p className="text-sm text-gray-400">@{user.username}</p>
        </div>
      </div>

      <form onSubmit={handleSaveProfile} className="bg-white border rounded-xl p-6 space-y-4 shadow-sm">
        <h2 className="font-semibold text-gray-700">Account details</h2>
        <div className="space-y-1.5">
          <Label>Username</Label>
          <Input value={user.username} disabled className="bg-gray-50 text-gray-400" />
        </div>
        <div className="space-y-1.5">
          <Label>Full name</Label>
          <Input value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Jane Doe" />
        </div>
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input type="email" value={email} onChange={e => setEmail(e.target.value)} />
        </div>
        <Button type="submit" loading={updateMe.isPending}>Save changes</Button>
      </form>

      <UserTokensSection />

      <form onSubmit={handleChangePassword} className="bg-white border rounded-xl p-6 space-y-4 shadow-sm">
        <h2 className="font-semibold text-gray-700">Change password</h2>
        <div className="space-y-1.5">
          <Label>Current password</Label>
          <Input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label>New password</Label>
          <Input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label>Confirm new password</Label>
          <Input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
        </div>
        <Button type="submit" loading={changePassword.isPending}>Change password</Button>
      </form>
    </div>
  )
}
