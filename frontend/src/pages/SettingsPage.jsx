import { useEffect, useState } from "react"
import { Save } from "lucide-react"
import { useMe } from "../hooks/useAuth"
import { useSettings, useUpdateSettings } from "../hooks/useSettings"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Skeleton } from "../components/ui/skeleton"
import { EmptyState } from "../components/ui/empty-state"
import { toast } from "sonner"

function Section({ title, description, children }) {
  return (
    <section className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <div className="space-y-3">{children}</div>
    </section>
  )
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-700">{label}</label>
      {children}
      {hint && <p className="text-[11px] text-gray-400">{hint}</p>}
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
      default_environment: form.default_environment || null,
      default_version_pattern: form.default_version_pattern || null,
      max_upload_mb: Number(form.max_upload_mb),
      notifications_retention_days: Number(form.notifications_retention_days),
      smtp_host: form.smtp_host || null,
      smtp_port: form.smtp_port ? Number(form.smtp_port) : null,
      smtp_user: form.smtp_user || null,
      smtp_from: form.smtp_from || null,
      smtp_use_tls: form.smtp_use_tls,
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
          <h1 className="text-2xl font-bold text-gray-800">Settings</h1>
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
        </form>
      </PageBody>
    </>
  )
}
