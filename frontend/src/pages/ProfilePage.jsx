import { useState, useEffect } from "react"
import { useMe, useUpdateMe, useChangePassword } from "../hooks/useAuth"
import { useUserTokens, useCreateUserToken, useRevokeUserToken } from "../hooks/useTokens"
import {
  useNotificationPreferences,
  useUpdateNotificationPreference,
} from "../hooks/useNotificationPreferences"
import { usePublicSettings } from "../hooks/useSettings"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { EmptyState } from "../components/ui/empty-state"
import { TimezonePicker } from "../components/ui/timezone-picker"
import { browserTimezone } from "../lib/format"
import { Trash2, Plus, Key, Copy, Eye, EyeOff, Clock, Bell, AlertTriangle, Globe } from "lucide-react"
import { toast } from "sonner"

const NOTIFICATION_EVENT_LABELS = {
  execution_assigned: {
    title: "Execution assigned to you",
    description: "When someone assigns you to a test execution.",
  },
  execution_finished: {
    title: "Execution finished",
    description: "When a run you created or are assigned to completes.",
  },
  execution_failed: {
    title: "Execution had failed tests",
    description: "When a completed run had at least one failed test.",
  },
}

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
        <code className="flex-1 bg-white dark:bg-gray-900 border rounded px-3 py-1.5 text-sm font-mono text-gray-800 dark:text-gray-100 truncate">
          {visible ? token : token.slice(0, 4) + "•".repeat(token.length - 4)}
        </code>
        <button onClick={() => setVisible(v => !v)} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1">
          {visible ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
        <button onClick={copy} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1"><Copy size={15} /></button>
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
    <div className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Key size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">API Tokens</h2>
      </div>

      {newToken && <NewTokenBanner token={newToken} onDone={() => setNewToken(null)} />}

      <form onSubmit={handleCreate} className="flex gap-2">
        <Input value={name} onChange={e => setName(e.target.value)} placeholder="Token name" className="flex-1" />
        <Button type="submit" size="sm" loading={create.isPending}><Plus size={14} /> New token</Button>
      </form>

      {tokens.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-400 dark:text-gray-500 uppercase">
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
                <td className="py-2 font-medium text-gray-800 dark:text-gray-100">{t.name}</td>
                <td className="py-2 font-mono text-gray-500 dark:text-gray-400">{t.prefix}…</td>
                <td className="py-2 text-gray-400 dark:text-gray-500 flex items-center gap-1"><Clock size={11} />{fmtDate(t.last_used_at)}</td>
                <td className="py-2 text-right">
                  <button onClick={() => handleRevoke(t.id)}
                    className="text-gray-300 dark:text-gray-600 hover:text-red-500 transition-colors p-1">
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

function DatePreferencesSection() {
  const { data: user } = useMe()
  const updateMe = useUpdateMe()
  const detectedBrowserTimezone = browserTimezone()
  const [timezone, setTimezone] = useState("")
  const [useRelative, setUseRelative] = useState(true)

  useEffect(() => {
    if (!user) return
    setTimezone(user.timezone ?? detectedBrowserTimezone ?? "UTC")
    setUseRelative(user.use_relative_dates ?? true)
  }, [user, detectedBrowserTimezone])

  const handleSave = async (event) => {
    event.preventDefault()
    try {
      await updateMe.mutateAsync({ timezone, use_relative_dates: useRelative })
      toast.success("Date preferences saved")
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? "Failed to save preferences")
    }
  }

  if (!user) return null

  return (
    <form onSubmit={handleSave} className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Globe size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">Dates &amp; timezone</h2>
      </div>
      <div className="space-y-1.5">
        <Label>Timezone</Label>
        <TimezonePicker value={timezone} onChange={setTimezone} />
        <p className="text-xs text-gray-400 dark:text-gray-500">All dates in the UI render in this timezone.</p>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <Label className="font-medium text-gray-800 dark:text-gray-100">Show relative dates</Label>
          <p className="text-xs text-gray-400 dark:text-gray-500">e.g. &ldquo;2 hours ago&rdquo;; hover shows the absolute timestamp.</p>
        </div>
        <input
          type="checkbox"
          aria-label="Show relative dates"
          checked={useRelative}
          onChange={event => setUseRelative(event.target.checked)}
          className="h-4 w-4 rounded border-gray-300 dark:border-gray-700 text-primary-600 focus:ring-primary-500"
        />
      </div>
      <Button type="submit" loading={updateMe.isPending}>Save preferences</Button>
    </form>
  )
}


function NotificationPreferencesSection() {
  const { data: preferences = [], isLoading } = useNotificationPreferences()
  const { data: publicSettings } = usePublicSettings()
  const update = useUpdateNotificationPreference()

  const smtpConfigured = publicSettings?.smtp_configured ?? true

  const togglePreference = async (preference, field) => {
    const next = { ...preference, [field]: !preference[field] }
    try {
      await update.mutateAsync({
        eventType: preference.event_type,
        in_app: next.in_app,
        email: next.email,
      })
      toast.success("Preferences saved")
    } catch {
      toast.error("Failed to save preference")
    }
  }

  const sortedPreferences = [...preferences].sort(
    (a, b) => a.event_type.localeCompare(b.event_type),
  )

  return (
    <div className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Bell size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">Notifications</h2>
      </div>

      {!smtpConfigured && (
        <div
          data-testid="smtp-not-configured-banner"
          className="flex items-start gap-2 text-xs bg-amber-50 border border-amber-200 rounded-md px-3 py-2 text-amber-800"
        >
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <p>SMTP is not configured. Emails will not be sent regardless of your preferences here.</p>
        </div>
      )}

      {isLoading && <p className="text-sm text-gray-400 dark:text-gray-500">Loading…</p>}

      {!isLoading && sortedPreferences.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-400 dark:text-gray-500 uppercase">
            <tr>
              <th className="text-left pb-2">Event</th>
              <th className="pb-2 w-16 text-center">In-app</th>
              <th className="pb-2 w-16 text-center">Email</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {sortedPreferences.map(preference => {
              const meta = NOTIFICATION_EVENT_LABELS[preference.event_type] ?? {
                title: preference.event_type,
                description: "",
              }
              return (
                <tr key={preference.event_type}>
                  <td className="py-3 pr-2">
                    <p className="font-medium text-gray-800 dark:text-gray-100">{meta.title}</p>
                    {meta.description && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{meta.description}</p>
                    )}
                  </td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      aria-label={`In-app for ${meta.title}`}
                      checked={preference.in_app}
                      onChange={() => togglePreference(preference, "in_app")}
                      disabled={update.isPending}
                      className="h-4 w-4 rounded border-gray-300 dark:border-gray-700 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      aria-label={`Email for ${meta.title}`}
                      checked={preference.email}
                      onChange={() => togglePreference(preference, "email")}
                      disabled={update.isPending || !smtpConfigured}
                      className="h-4 w-4 rounded border-gray-300 dark:border-gray-700 text-primary-600 focus:ring-primary-500 disabled:opacity-50"
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
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
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Profile</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Manage your account settings</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-2xl font-bold">
          {initials}
        </div>
        <div>
          <p className="font-semibold text-gray-800 dark:text-gray-100 text-lg">{user.full_name || user.username}</p>
          <p className="text-sm text-gray-400 dark:text-gray-500">@{user.username}</p>
        </div>
      </div>

      <form onSubmit={handleSaveProfile} className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">Account details</h2>
        <div className="space-y-1.5">
          <Label>Username</Label>
          <Input value={user.username} disabled className="bg-gray-50 dark:bg-gray-900 text-gray-400 dark:text-gray-500" />
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

      <DatePreferencesSection />

      <NotificationPreferencesSection />

      <form onSubmit={handleChangePassword} className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">Change password</h2>
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
