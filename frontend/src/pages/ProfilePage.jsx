import { useState, useEffect } from "react"
import { useTranslation } from "react-i18next"
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
import { useTheme, DARK_VARIANTS } from "../hooks/useTheme"
import { useLocale } from "../hooks/useLocale"
import { SUPPORTED_LOCALES } from "../i18n"
import { Trash2, Plus, Key, Copy, Eye, EyeOff, Clock, Bell, AlertTriangle, Globe, Palette, Sun, Moon, Monitor, Languages } from "lucide-react"
import { toast } from "sonner"

function fmtDate(iso, fallback) {
  if (!iso) return fallback
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

function NewTokenBanner({ token, onDone }) {
  const { t } = useTranslation(["profile", "common"])
  const [visible, setVisible] = useState(false)
  const copy = () => { navigator.clipboard.writeText(token); toast.success(t("tokens.copied")) }
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
      <p className="text-sm font-medium text-green-800">{t("tokens.created")}</p>
      <div className="flex items-center gap-2">
        <code className="flex-1 bg-white dark:bg-gray-900 border rounded px-3 py-1.5 text-sm font-mono text-gray-800 dark:text-gray-100 truncate">
          {visible ? token : token.slice(0, 4) + "•".repeat(token.length - 4)}
        </code>
        <button onClick={() => setVisible(v => !v)} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1">
          {visible ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
        <button onClick={copy} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1"><Copy size={15} /></button>
      </div>
      <Button size="sm" variant="outline" onClick={onDone}>{t("common:actions.done")}</Button>
    </div>
  )
}

function UserTokensSection() {
  const { t } = useTranslation(["profile", "common"])
  const { data: tokens = [] } = useUserTokens()
  const create = useCreateUserToken()
  const revoke = useRevokeUserToken()
  const [name, setName] = useState("")
  const [newToken, setNewToken] = useState(null)

  const handleCreate = async (event) => {
    event.preventDefault()
    if (!name.trim()) return
    try {
      const created = await create.mutateAsync({ name: name.trim() })
      setNewToken(created.token)
      setName("")
    } catch {
      toast.error(t("tokens.createFailed"))
    }
  }

  const handleRevoke = async (id) => {
    try {
      await revoke.mutateAsync(id)
      toast.success(t("tokens.revoked"))
    } catch {
      toast.error(t("tokens.revokeFailed"))
    }
  }

  return (
    <div className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Key size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">{t("tokens.title")}</h2>
      </div>

      {newToken && <NewTokenBanner token={newToken} onDone={() => setNewToken(null)} />}

      <form onSubmit={handleCreate} className="flex gap-2">
        <Input value={name} onChange={event => setName(event.target.value)} placeholder={t("tokens.namePlaceholder")} className="flex-1" />
        <Button type="submit" size="sm" loading={create.isPending}><Plus size={14} /> {t("tokens.newToken")}</Button>
      </form>

      {tokens.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-400 dark:text-gray-500 uppercase">
            <tr>
              <th className="text-left pb-2">{t("tokens.headers.name")}</th>
              <th className="text-left pb-2">{t("tokens.headers.prefix")}</th>
              <th className="text-left pb-2">{t("tokens.headers.lastUsed")}</th>
              <th />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {tokens.map(token => (
              <tr key={token.id}>
                <td className="py-2 font-medium text-gray-800 dark:text-gray-100">{token.name}</td>
                <td className="py-2 font-mono text-gray-500 dark:text-gray-400">{token.prefix}…</td>
                <td className="py-2 text-gray-400 dark:text-gray-500 flex items-center gap-1"><Clock size={11} />{fmtDate(token.last_used_at, t("common:time.never"))}</td>
                <td className="py-2 text-right">
                  <button onClick={() => handleRevoke(token.id)}
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
          title={t("tokens.empty.title")}
          description={t("tokens.empty.description")}
          compact
        />
      )}
    </div>
  )
}

function DatePreferencesSection() {
  const { t } = useTranslation("profile")
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
      toast.success(t("dates.saved"))
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("dates.saveFailed"))
    }
  }

  if (!user) return null

  return (
    <form onSubmit={handleSave} className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Globe size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">{t("dates.title")}</h2>
      </div>
      <div className="space-y-1.5">
        <Label>{t("dates.timezone")}</Label>
        <TimezonePicker value={timezone} onChange={setTimezone} />
        <p className="text-xs text-gray-400 dark:text-gray-500">{t("dates.timezoneHint")}</p>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <Label className="font-medium text-gray-800 dark:text-gray-100">{t("dates.showRelative")}</Label>
          <p className="text-xs text-gray-400 dark:text-gray-500">{t("dates.showRelativeHint")}</p>
        </div>
        <input
          type="checkbox"
          aria-label={t("dates.showRelative")}
          checked={useRelative}
          onChange={event => setUseRelative(event.target.checked)}
          className="h-4 w-4 rounded border-gray-300 dark:border-gray-700 text-primary-600 focus:ring-primary-500"
        />
      </div>
      <Button type="submit" loading={updateMe.isPending}>{t("dates.savePreferences")}</Button>
    </form>
  )
}


const THEME_MODE_ICONS = { light: Sun, dark: Moon, system: Monitor }
const THEME_MODES = ["light", "dark", "system"]

const VARIANT_SWATCHES = {
  default: ["#030712", "#111827", "#374151", "#f3f4f6"],
  navy:    ["#1e2a3d", "#28354c", "#4a5a78", "#e6edf6"],
  dim:     ["#1c2128", "#22272e", "#444c56", "#adbac7"],
}

function VariantSwatch({ name }) {
  const colors = VARIANT_SWATCHES[name]
  return (
    <div className="flex h-6 rounded-md overflow-hidden border border-gray-200 dark:border-gray-700">
      {colors.map((color, index) => (
        <div key={index} className="flex-1" style={{ backgroundColor: color }} />
      ))}
    </div>
  )
}

function AppearanceSection() {
  const { t } = useTranslation(["profile", "common"])
  const { theme, variant, setTheme, setVariant } = useTheme()
  const { locale, setLocale } = useLocale()

  return (
    <section className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Palette size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">{t("appearance.title")}</h2>
      </div>

      <div className="space-y-1.5">
        <Label>{t("appearance.language")}</Label>
        <div role="radiogroup" aria-label={t("appearance.language")} className="grid grid-cols-2 gap-2">
          {SUPPORTED_LOCALES.map(code => {
            const active = locale === code
            return (
              <button
                key={code}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => setLocale(code)}
                className={`flex items-center justify-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors ${
                  active
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                    : "border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
                }`}
              >
                <Languages size={14} /> {t(`common:language.${code}`)}
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-1.5">
        <Label>{t("appearance.mode")}</Label>
        <div role="radiogroup" aria-label={t("appearance.mode")} className="grid grid-cols-3 gap-2">
          {THEME_MODES.map(value => {
            const Icon = THEME_MODE_ICONS[value]
            const active = theme === value
            return (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => setTheme(value)}
                className={`flex items-center justify-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors ${
                  active
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                    : "border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
                }`}
              >
                <Icon size={14} /> {t(`appearance.modes.${value}`)}
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-1.5">
        <Label>{t("appearance.variant")}</Label>
        <p className="text-xs text-gray-400 dark:text-gray-500">{t("appearance.variantHint")}</p>
        <div role="radiogroup" aria-label={t("appearance.variant")} className="space-y-2">
          {DARK_VARIANTS.map(name => {
            const active = variant === name
            return (
              <button
                key={name}
                type="button"
                role="radio"
                aria-checked={active}
                onClick={() => setVariant(name)}
                className={`w-full text-left px-3 py-2 rounded-md border transition-colors ${
                  active
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-900/30"
                    : "border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-1.5">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{t(`appearance.variants.${name}.label`)}</span>
                  {active && <span className="text-xs text-primary-600 dark:text-primary-300">{t("appearance.selected")}</span>}
                </div>
                <VariantSwatch name={name} />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">{t(`appearance.variants.${name}.description`)}</p>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}


function NotificationPreferencesSection() {
  const { t } = useTranslation("profile")
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
      toast.success(t("notifications.saved"))
    } catch {
      toast.error(t("notifications.saveFailed"))
    }
  }

  const sortedPreferences = [...preferences].sort(
    (a, b) => a.event_type.localeCompare(b.event_type),
  )

  return (
    <div className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <Bell size={15} className="text-gray-500 dark:text-gray-400" />
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">{t("notifications.title")}</h2>
      </div>

      {!smtpConfigured && (
        <div
          data-testid="smtp-not-configured-banner"
          className="flex items-start gap-2 text-xs bg-amber-50 border border-amber-200 rounded-md px-3 py-2 text-amber-800"
        >
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <p>{t("notifications.smtpDisabledWarning")}</p>
        </div>
      )}

      {isLoading && <p className="text-sm text-gray-400 dark:text-gray-500">{t("common:actions.loading", { ns: "common" })}</p>}

      {!isLoading && sortedPreferences.length > 0 && (
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-400 dark:text-gray-500 uppercase">
            <tr>
              <th className="text-left pb-2">{t("notifications.headers.event")}</th>
              <th className="pb-2 w-16 text-center">{t("notifications.headers.inApp")}</th>
              <th className="pb-2 w-16 text-center">{t("notifications.headers.email")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {sortedPreferences.map(preference => {
              const eventKey = `notifications.events.${preference.event_type}`
              const eventTitle = t(`${eventKey}.title`, { defaultValue: preference.event_type })
              const eventDescription = t(`${eventKey}.description`, { defaultValue: "" })
              return (
                <tr key={preference.event_type}>
                  <td className="py-3 pr-2">
                    <p className="font-medium text-gray-800 dark:text-gray-100">{eventTitle}</p>
                    {eventDescription && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{eventDescription}</p>
                    )}
                  </td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      aria-label={t("notifications.inAppFor", { title: eventTitle })}
                      checked={preference.in_app}
                      onChange={() => togglePreference(preference, "in_app")}
                      disabled={update.isPending}
                      className="h-4 w-4 rounded border-gray-300 dark:border-gray-700 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                  <td className="py-3 text-center">
                    <input
                      type="checkbox"
                      aria-label={t("notifications.emailFor", { title: eventTitle })}
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
  const { t } = useTranslation(["profile", "common"])
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

  const handleSaveProfile = async (event) => {
    event.preventDefault()
    await updateMe.mutateAsync({ full_name: fullName || null, email })
    toast.success(t("account.saved"))
  }

  const handleChangePassword = async (event) => {
    event.preventDefault()
    if (newPassword !== confirmPassword) return toast.error(t("password.mismatch"))
    if (newPassword.length < 8) return toast.error(t("password.tooShort"))
    try {
      await changePassword.mutateAsync({ current_password: currentPassword, new_password: newPassword })
      toast.success(t("password.saved"))
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("password.failed"))
    }
  }

  if (!user) return null

  const initials = (user.full_name ?? user.username)
    .split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()

  return (
    <div className="pl-14 pr-4 py-4 md:p-8 max-w-lg space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{t("subtitle")}</p>
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
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">{t("account.title")}</h2>
        <div className="space-y-1.5">
          <Label>{t("account.username")}</Label>
          <Input value={user.username} disabled className="bg-gray-50 dark:bg-gray-900 text-gray-400 dark:text-gray-500" />
        </div>
        <div className="space-y-1.5">
          <Label>{t("account.fullName")}</Label>
          <Input value={fullName} onChange={event => setFullName(event.target.value)} placeholder={t("account.fullNamePlaceholder")} />
        </div>
        <div className="space-y-1.5">
          <Label>{t("account.email")}</Label>
          <Input type="email" value={email} onChange={event => setEmail(event.target.value)} />
        </div>
        <Button type="submit" loading={updateMe.isPending}>{t("common:actions.saveChanges")}</Button>
      </form>

      <UserTokensSection />

      <DatePreferencesSection />

      <AppearanceSection />

      <NotificationPreferencesSection />

      <form onSubmit={handleChangePassword} className="bg-white dark:bg-gray-900 border rounded-xl p-6 space-y-4 shadow-sm">
        <h2 className="font-semibold text-gray-700 dark:text-gray-200">{t("password.title")}</h2>
        <div className="space-y-1.5">
          <Label>{t("password.current")}</Label>
          <Input type="password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label>{t("password.new")}</Label>
          <Input type="password" value={newPassword} onChange={event => setNewPassword(event.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label>{t("password.confirm")}</Label>
          <Input type="password" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} />
        </div>
        <Button type="submit" loading={changePassword.isPending}>{t("password.submit")}</Button>
      </form>
    </div>
  )
}
