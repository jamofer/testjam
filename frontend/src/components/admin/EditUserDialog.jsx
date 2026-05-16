import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { usersApi } from "../../api/users"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { TimezonePicker } from "../ui/timezone-picker"
import { ResetPasswordDialog } from "./ResetPasswordDialog"

export function EditUserDialog({ user, open, onOpenChange }) {
  const { t } = useTranslation("admin")
  const queryClient = useQueryClient()
  const [form, setForm] = useState(() => formFromUser(user))
  const [resetOpen, setResetOpen] = useState(false)

  const update = useMutation({
    mutationFn: (payload) => usersApi.update(user.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.success(t("users.edit.updated"))
      onOpenChange(false)
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      toast.error(typeof detail === "string" ? detail : t("users.edit.updateFailed"))
    },
  })

  const handleField = (key) => (event) => {
    const value = event.target.type === "checkbox" ? event.target.checked : event.target.value
    setForm((current) => ({ ...current, [key]: value }))
  }

  const submit = () => update.mutate(diffPayload(user, form))

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("users.edit.title", { username: user.username })}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Field label={t("users.edit.username")}>
              <Input value={form.username} onChange={handleField("username")} />
            </Field>
            <Field label={t("users.edit.email")}>
              <Input type="email" value={form.email} onChange={handleField("email")} />
            </Field>
            <Field label={t("users.edit.fullName")}>
              <Input value={form.full_name} onChange={handleField("full_name")} />
            </Field>
            <Field label={t("users.edit.timezone")}>
              <TimezonePicker
                value={form.timezone}
                onChange={(zone) => setForm((current) => ({ ...current, timezone: zone }))}
              />
            </Field>
            <div className="flex gap-6 pt-1 text-sm">
              <Toggle label={t("users.edit.active")} checked={form.is_active} onChange={handleField("is_active")} />
              <Toggle label={t("users.edit.admin")} checked={form.is_admin} onChange={handleField("is_admin")} />
            </div>
            <div className="flex justify-between pt-3 border-t">
              <Button variant="outline" size="sm" onClick={() => setResetOpen(true)}>
                {t("users.edit.resetPassword")}
              </Button>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => onOpenChange(false)}>{t("users.edit.cancel")}</Button>
                <Button onClick={submit} disabled={update.isPending}>{t("users.edit.save")}</Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      {resetOpen && (
        <ResetPasswordDialog
          user={user}
          onClose={() => setResetOpen(false)}
        />
      )}
    </>
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

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" checked={checked} onChange={onChange} />
      {label}
    </label>
  )
}

function formFromUser(user) {
  return {
    username: user.username ?? "",
    email: user.email ?? "",
    full_name: user.full_name ?? "",
    timezone: user.timezone ?? "",
    is_active: !!user.is_active,
    is_admin: !!user.is_admin,
  }
}

function diffPayload(user, form) {
  const payload = {}
  for (const key of ["username", "email", "full_name", "timezone"]) {
    const original = user[key] ?? ""
    if ((form[key] ?? "") !== original) {
      payload[key] = form[key] === "" ? null : form[key]
    }
  }
  if (!!user.is_active !== form.is_active) payload.is_active = form.is_active
  if (!!user.is_admin !== form.is_admin) payload.is_admin = form.is_admin
  return payload
}
