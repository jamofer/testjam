import { useEffect, useRef, useState } from "react"
import { Download, Save, Upload } from "lucide-react"
import { useMe } from "../hooks/useAuth"
import { useSettings, useUpdateSettings } from "../hooks/useSettings"
import { settingsApi } from "../api/settings"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Skeleton } from "../components/ui/skeleton"
import { EmptyState } from "../components/ui/empty-state"
import { toast } from "sonner"

const RESTORE_CONFIRM_PHRASE = "REPLACE ALL DATA"

function Section({ title, description, children }) {
  return (
    <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">{title}</h2>
        {description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
      </div>
      <div className="space-y-3">{children}</div>
    </section>
  )
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-700 dark:text-gray-200">{label}</label>
      {children}
      {hint && <p className="text-[11px] text-gray-400 dark:text-gray-500">{hint}</p>}
    </div>
  )
}

function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-2 text-sm cursor-pointer">
      <input type="checkbox" checked={!!checked} onChange={e => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  )
}

export function SettingsPage() {
  const { data: me } = useMe()
  const { data: settings, isLoading } = useSettings()
  const updateSettings = useUpdateSettings()
  const [form, setForm] = useState(null)

  useEffect(() => {
    if (settings) {
      setForm({
        site_url: settings.site_url ?? "",
        app_name: settings.app_name ?? "",
        allow_registration: settings.allow_registration,
        allow_user_self_delete: settings.allow_user_self_delete ?? false,
        default_environment: settings.default_environment ?? "",
        default_version_pattern: settings.default_version_pattern ?? "",
        max_upload_mb: settings.max_upload_mb,
        notifications_retention_days: settings.notifications_retention_days,
        smtp_host: settings.smtp_host ?? "",
        smtp_port: settings.smtp_port ?? "",
        smtp_user: settings.smtp_user ?? "",
        smtp_password: "",
        clear_smtp_password: false,
        smtp_from: settings.smtp_from ?? "",
        smtp_use_tls: settings.smtp_use_tls,
        ws_log_flush_ms: settings.ws_log_flush_ms ?? 100,
      })
    }
  }, [settings])

  if (me && !me.is_admin) {
    return (
      <PageBody>
        <EmptyState
          title="Admin only"
          description="Settings are only visible to administrators."
        />
      </PageBody>
    )
  }

  if (isLoading || !form) {
    return (
      <PageBody>
        <div className="max-w-2xl space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
      </PageBody>
    )
  }

  const set = (k) => (v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    const payload = {
      site_url: form.site_url || null,
      app_name: form.app_name,
      allow_registration: form.allow_registration,
      allow_user_self_delete: form.allow_user_self_delete,
      default_environment: form.default_environment || null,
      default_version_pattern: form.default_version_pattern || null,
      max_upload_mb: Number(form.max_upload_mb),
      notifications_retention_days: Number(form.notifications_retention_days),
      smtp_host: form.smtp_host || null,
      smtp_port: form.smtp_port ? Number(form.smtp_port) : null,
      smtp_user: form.smtp_user || null,
      smtp_from: form.smtp_from || null,
      smtp_use_tls: form.smtp_use_tls,
      ws_log_flush_ms: Number(form.ws_log_flush_ms),
    }
    if (form.clear_smtp_password) payload.smtp_password = ""
    else if (form.smtp_password) payload.smtp_password = form.smtp_password

    try {
      await updateSettings.mutateAsync(payload)
      toast.success("Settings saved")
      setForm(f => ({ ...f, smtp_password: "", clear_smtp_password: false }))
    } catch {
      toast.error("Failed to save settings")
    }
  }

  return (
    <>
      <PageHeader crumbs={[{ label: "Settings" }]}>
        <div className="max-w-2xl flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Settings</h1>
          <Button size="sm" onClick={submit} loading={updateSettings.isPending} className="self-start sm:self-auto">
            <Save size={13} /> Save
          </Button>
        </div>
      </PageHeader>

      <PageBody>
        <form onSubmit={submit} className="max-w-2xl space-y-4">

          <Section title="General"
            description="Branding and the public URL used in shared links and HTML reports.">
            <Field label="Site URL"
              hint="If set, attachments and 'View in app' links use this URL instead of the request host.">
              <Input value={form.site_url} onChange={e => set("site_url")(e.target.value)}
                placeholder="https://qa.example.com" />
            </Field>
            <Field label="App name">
              <Input value={form.app_name} onChange={e => set("app_name")(e.target.value)} />
            </Field>
            <Toggle checked={form.allow_registration}
              onChange={set("allow_registration")}
              label="Allow new user self-registration" />
            <Toggle checked={form.allow_user_self_delete}
              onChange={set("allow_user_self_delete")}
              label="Allow users to delete their own account" />
          </Section>

          <Section title="Execution defaults">
            <Field label="Default environment">
              <Input value={form.default_environment} onChange={e => set("default_environment")(e.target.value)}
                placeholder="staging" />
            </Field>
            <Field label="Default version pattern">
              <Input value={form.default_version_pattern} onChange={e => set("default_version_pattern")(e.target.value)}
                placeholder="vYYYY.MM.DD" />
            </Field>
          </Section>

          <Section title="Limits">
            <Field label="Max upload size (MB)">
              <Input type="number" min="1" value={form.max_upload_mb}
                onChange={e => set("max_upload_mb")(e.target.value)} />
            </Field>
            <Field label="Notifications retention (days)"
              hint="Older notifications are purged.">
              <Input type="number" min="1" value={form.notifications_retention_days}
                onChange={e => set("notifications_retention_days")(e.target.value)} />
            </Field>
          </Section>

          <Section title="Email (SMTP)"
            description="Outgoing notifications. Leave host empty to disable email.">
            <Field label="SMTP host">
              <Input value={form.smtp_host} onChange={e => set("smtp_host")(e.target.value)}
                placeholder="smtp.example.com" />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Port">
                <Input type="number" value={form.smtp_port} onChange={e => set("smtp_port")(e.target.value)}
                  placeholder="587" />
              </Field>
              <Field label="From address">
                <Input value={form.smtp_from} onChange={e => set("smtp_from")(e.target.value)}
                  placeholder="noreply@example.com" />
              </Field>
            </div>
            <Field label="Username">
              <Input value={form.smtp_user} onChange={e => set("smtp_user")(e.target.value)} />
            </Field>
            <Field label="Password"
              hint={settings.smtp_password_set
                ? "A password is configured. Type a new one to replace it, or check 'Clear password' to remove."
                : "No password set."}>
              <Input type="password" value={form.smtp_password}
                onChange={e => set("smtp_password")(e.target.value)}
                placeholder={settings.smtp_password_set ? "•••••••• (set)" : ""}
                disabled={form.clear_smtp_password} />
            </Field>
            {settings.smtp_password_set && (
              <Toggle checked={form.clear_smtp_password}
                onChange={set("clear_smtp_password")}
                label="Clear stored password on save" />
            )}
            <Toggle checked={form.smtp_use_tls}
              onChange={set("smtp_use_tls")}
              label="Use STARTTLS" />
          </Section>

          <Section title="Real-time"
            description="Tuning for WebSocket broadcasts during live test runs.">
            <Field label="Log flush interval (ms)"
              hint="How often buffered log lines are pushed to subscribers. 0 disables batching.">
              <Input type="number" min="0" value={form.ws_log_flush_ms}
                onChange={e => set("ws_log_flush_ms")(e.target.value)} />
            </Field>
          </Section>
        </form>

        <div className="max-w-2xl mt-4">
          <BackupRestoreSection />
        </div>
      </PageBody>
    </>
  )
}

function BackupRestoreSection() {
  const [downloading, setDownloading] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [confirmText, setConfirmText] = useState("")
  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await settingsApi.downloadBackup()
      toast.success("Backup downloaded")
    } catch {
      toast.error("Backup failed")
    } finally {
      setDownloading(false)
    }
  }

  const canRestore = !!selectedFile && confirmText === RESTORE_CONFIRM_PHRASE

  const handleRestore = async () => {
    if (!canRestore) return
    setRestoring(true)
    try {
      const summary = await settingsApi.restoreBackup(selectedFile)
      toast.success(`Restored (${summary.uploads_restored} files)`)
      setSelectedFile(null)
      setConfirmText("")
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Restore failed")
    } finally {
      setRestoring(false)
    }
  }

  return (
    <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Backup &amp; Restore</h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          Download a ZIP containing the database dump and uploaded files. Restore replaces all data.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Button size="sm" onClick={handleDownload} loading={downloading}>
          <Download size={13} /> Download backup
        </Button>
      </div>

      <div className="border-t pt-4 space-y-3">
        <p className="text-xs font-medium text-red-600">
          Restore is destructive. The current database and uploads are overwritten.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,application/zip"
          onChange={e => setSelectedFile(e.target.files?.[0] ?? null)}
          className="text-xs"
        />
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-700 dark:text-gray-200">
            Type <code className="px-1 bg-gray-100 dark:bg-gray-800 rounded">{RESTORE_CONFIRM_PHRASE}</code> to confirm
          </label>
          <Input value={confirmText} onChange={e => setConfirmText(e.target.value)} placeholder={RESTORE_CONFIRM_PHRASE} />
        </div>
        <Button size="sm" variant="outline" onClick={handleRestore}
          loading={restoring} disabled={!canRestore}>
          <Upload size={13} /> Restore from backup
        </Button>
      </div>
    </section>
  )
}
