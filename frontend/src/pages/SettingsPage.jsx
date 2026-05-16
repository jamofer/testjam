import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
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
      <input type="checkbox" checked={!!checked} onChange={event => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  )
}

export function SettingsPage() {
  const { t } = useTranslation(["admin", "nav"])
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
          title={t("settings.adminOnly")}
          description={t("settings.adminOnlyDescription")}
        />
      </PageBody>
    )
  }

  if (isLoading || !form) {
    return (
      <PageBody>
        <div className="max-w-2xl space-y-4">
          {[1, 2, 3].map(index => <Skeleton key={index} className="h-32 w-full" />)}
        </div>
      </PageBody>
    )
  }

  const set = (key) => (value) => setForm(prev => ({ ...prev, [key]: value }))

  const submit = async (event) => {
    event.preventDefault()
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
      toast.success(t("settings.saved"))
      setForm(prev => ({ ...prev, smtp_password: "", clear_smtp_password: false }))
    } catch {
      toast.error(t("settings.saveFailed"))
    }
  }

  return (
    <>
      <PageHeader crumbs={[{ label: t("nav:user.settings") }]}>
        <div className="max-w-2xl flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("settings.title")}</h1>
          <Button size="sm" onClick={submit} loading={updateSettings.isPending} className="self-start sm:self-auto">
            <Save size={13} /> {t("settings.save")}
          </Button>
        </div>
      </PageHeader>

      <PageBody>
        <form onSubmit={submit} className="max-w-2xl space-y-4">

          <Section title={t("settings.sections.general.title")}
            description={t("settings.sections.general.description")}>
            <Field label={t("settings.sections.general.siteUrl")}
              hint={t("settings.sections.general.siteUrlHint")}>
              <Input value={form.site_url} onChange={event => set("site_url")(event.target.value)}
                placeholder={t("settings.sections.general.siteUrlPlaceholder")} />
            </Field>
            <Field label={t("settings.sections.general.appName")}>
              <Input value={form.app_name} onChange={event => set("app_name")(event.target.value)} />
            </Field>
            <Toggle checked={form.allow_registration}
              onChange={set("allow_registration")}
              label={t("settings.sections.general.allowRegistration")} />
            <Toggle checked={form.allow_user_self_delete}
              onChange={set("allow_user_self_delete")}
              label={t("settings.sections.general.allowSelfDelete")} />
          </Section>

          <Section title={t("settings.sections.executionDefaults.title")}>
            <Field label={t("settings.sections.executionDefaults.defaultEnvironment")}>
              <Input value={form.default_environment} onChange={event => set("default_environment")(event.target.value)}
                placeholder={t("settings.sections.executionDefaults.defaultEnvironmentPlaceholder")} />
            </Field>
            <Field label={t("settings.sections.executionDefaults.defaultVersionPattern")}>
              <Input value={form.default_version_pattern} onChange={event => set("default_version_pattern")(event.target.value)}
                placeholder={t("settings.sections.executionDefaults.defaultVersionPatternPlaceholder")} />
            </Field>
          </Section>

          <Section title={t("settings.sections.limits.title")}>
            <Field label={t("settings.sections.limits.maxUpload")}>
              <Input type="number" min="1" value={form.max_upload_mb}
                onChange={event => set("max_upload_mb")(event.target.value)} />
            </Field>
            <Field label={t("settings.sections.limits.notificationsRetention")}
              hint={t("settings.sections.limits.notificationsRetentionHint")}>
              <Input type="number" min="1" value={form.notifications_retention_days}
                onChange={event => set("notifications_retention_days")(event.target.value)} />
            </Field>
          </Section>

          <Section title={t("settings.sections.smtp.title")}
            description={t("settings.sections.smtp.description")}>
            <Field label={t("settings.sections.smtp.host")}>
              <Input value={form.smtp_host} onChange={event => set("smtp_host")(event.target.value)}
                placeholder={t("settings.sections.smtp.hostPlaceholder")} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("settings.sections.smtp.port")}>
                <Input type="number" value={form.smtp_port} onChange={event => set("smtp_port")(event.target.value)}
                  placeholder={t("settings.sections.smtp.portPlaceholder")} />
              </Field>
              <Field label={t("settings.sections.smtp.from")}>
                <Input value={form.smtp_from} onChange={event => set("smtp_from")(event.target.value)}
                  placeholder={t("settings.sections.smtp.fromPlaceholder")} />
              </Field>
            </div>
            <Field label={t("settings.sections.smtp.user")}>
              <Input value={form.smtp_user} onChange={event => set("smtp_user")(event.target.value)} />
            </Field>
            <Field label={t("settings.sections.smtp.password")}
              hint={settings.smtp_password_set
                ? t("settings.sections.smtp.passwordSetHint")
                : t("settings.sections.smtp.noPasswordHint")}>
              <Input type="password" value={form.smtp_password}
                onChange={event => set("smtp_password")(event.target.value)}
                placeholder={settings.smtp_password_set ? t("settings.sections.smtp.passwordPlaceholderSet") : ""}
                disabled={form.clear_smtp_password} />
            </Field>
            {settings.smtp_password_set && (
              <Toggle checked={form.clear_smtp_password}
                onChange={set("clear_smtp_password")}
                label={t("settings.sections.smtp.clearPassword")} />
            )}
            <Toggle checked={form.smtp_use_tls}
              onChange={set("smtp_use_tls")}
              label={t("settings.sections.smtp.useTls")} />
          </Section>

          <Section title={t("settings.sections.realtime.title")}
            description={t("settings.sections.realtime.description")}>
            <Field label={t("settings.sections.realtime.logFlush")}
              hint={t("settings.sections.realtime.logFlushHint")}>
              <Input type="number" min="0" value={form.ws_log_flush_ms}
                onChange={event => set("ws_log_flush_ms")(event.target.value)} />
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
  const { t } = useTranslation("admin")
  const [downloading, setDownloading] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [confirmText, setConfirmText] = useState("")
  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await settingsApi.downloadBackup()
      toast.success(t("settings.backup.downloaded"))
    } catch {
      toast.error(t("settings.backup.downloadFailed"))
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
      toast.success(t("settings.backup.restored", { count: summary.uploads_restored }))
      setSelectedFile(null)
      setConfirmText("")
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("settings.backup.restoreFailed"))
    } finally {
      setRestoring(false)
    }
  }

  return (
    <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">{t("settings.backup.title")}</h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t("settings.backup.intro")}</p>
      </div>

      <div className="flex items-center gap-3">
        <Button size="sm" onClick={handleDownload} loading={downloading}>
          <Download size={13} /> {t("settings.backup.download")}
        </Button>
      </div>

      <div className="border-t pt-4 space-y-3">
        <p className="text-xs font-medium text-red-600">{t("settings.backup.destructive")}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,application/zip"
          onChange={event => setSelectedFile(event.target.files?.[0] ?? null)}
          className="text-xs"
        />
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-700 dark:text-gray-200">
            {t("settings.backup.confirmLabel", { phrase: RESTORE_CONFIRM_PHRASE })}
          </label>
          <Input value={confirmText} onChange={event => setConfirmText(event.target.value)} placeholder={RESTORE_CONFIRM_PHRASE} />
        </div>
        <Button size="sm" variant="outline" onClick={handleRestore}
          loading={restoring} disabled={!canRestore}>
          <Upload size={13} /> {t("settings.backup.restoreButton")}
        </Button>
      </div>
    </section>
  )
}
