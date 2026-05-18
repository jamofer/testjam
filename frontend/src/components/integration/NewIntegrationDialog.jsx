import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { useCreateIntegration, useIntegrationProviders } from "../../hooks/useIntegrations"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog"

import { PROVIDER_FIELDS, buildProviderConfig } from "./providerSchemas"


export function NewIntegrationDialog({ projectId, onClose }) {
  const { t } = useTranslation("integrations")
  const { data: providers = [] } = useIntegrationProviders()
  const create = useCreateIntegration(projectId)
  const [step, setStep] = useState(0)
  const [provider, setProvider] = useState("")
  const [name, setName] = useState("")
  const [secret, setSecret] = useState("")
  const [configFields, setConfigFields] = useState({})

  const fields = useMemo(() => PROVIDER_FIELDS[provider] ?? [], [provider])
  const configValid = fields.every(field => !field.required || configFields[field.key])
  const canSubmit = provider && name.trim() && secret && configValid

  const submit = async (event) => {
    event.preventDefault()
    if (!canSubmit) return
    try {
      await create.mutateAsync({
        provider,
        name: name.trim(),
        config: buildProviderConfig(provider, configFields),
        secret,
        is_active: true,
      })
      toast.success(t("trackers.created"))
      onClose()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("trackers.createFailed"))
    }
  }

  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("trackers.dialog.title")}</DialogTitle>
        </DialogHeader>

        {step === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-gray-600 dark:text-gray-300">{t("trackers.dialog.pickProvider")}</p>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {providers.filter(option => option.key !== "fake").map(option => (
                <li key={option.key}>
                  <button
                    type="button"
                    onClick={() => { setProvider(option.key); setStep(1) }}
                    className={`w-full text-left border rounded-lg px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 ${
                      provider === option.key ? "border-primary-500" : "border-gray-200 dark:border-gray-700"
                    }`}
                  >
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{option.label}</span>
                    <span className="block text-xs text-gray-500 dark:text-gray-400 font-mono">{option.key}</span>
                  </button>
                </li>
              ))}
            </ul>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={onClose}>{t("actions.cancel")}</Button>
            </DialogFooter>
          </div>
        )}

        {step === 1 && (
          <form className="space-y-3" onSubmit={(event) => { event.preventDefault(); setStep(2) }}>
            <div className="space-y-1">
              <Label>{t("trackers.dialog.name")}</Label>
              <Input
                value={name}
                onChange={event => setName(event.target.value)}
                placeholder={t("trackers.dialog.namePlaceholder")}
                required
              />
            </div>
            {fields.map(field => (
              <div key={field.key} className="space-y-1">
                <Label>{t(`trackers.fields.${provider}.${field.key}`, field.label)}</Label>
                <Input
                  value={configFields[field.key] ?? ""}
                  onChange={event => setConfigFields(prev => ({ ...prev, [field.key]: event.target.value }))}
                  placeholder={field.placeholder ?? ""}
                  required={field.required}
                />
                {field.help && (
                  <p className="text-xs text-gray-400 dark:text-gray-500">
                    {t(`trackers.help.${provider}.${field.key}`, field.help)}
                  </p>
                )}
              </div>
            ))}
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setStep(0)}>{t("actions.back")}</Button>
              <Button type="submit" disabled={!name.trim() || !configValid}>{t("actions.next")}</Button>
            </DialogFooter>
          </form>
        )}

        {step === 2 && (
          <form className="space-y-3" onSubmit={submit}>
            <div className="space-y-1">
              <Label>{t("trackers.dialog.secret")}</Label>
              <Input
                type="password"
                value={secret}
                onChange={event => setSecret(event.target.value)}
                placeholder={t("trackers.dialog.secretPlaceholder")}
                required
              />
              <p className="text-xs text-gray-400 dark:text-gray-500">{t("trackers.dialog.secretHelp")}</p>
            </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setStep(1)}>{t("actions.back")}</Button>
              <Button type="submit" disabled={!canSubmit || create.isPending}>
                {t("trackers.dialog.create")}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
