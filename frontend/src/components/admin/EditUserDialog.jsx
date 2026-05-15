import { useState } from "react"
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
  const queryClient = useQueryClient()
  const [form, setForm] = useState(() => formFromUser(user))
  const [resetOpen, setResetOpen] = useState(false)

  const update = useMutation({
    mutationFn: (payload) => usersApi.update(user.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.success("User updated")
      onOpenChange(false)
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail
      toast.error(typeof detail === "string" ? detail : "Failed to update user")
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
            <DialogTitle>Edit user "{user.username}"</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Field label="Username">
              <Input value={form.username} onChange={handleField("username")} />
            </Field>
            <Field label="Email">
              <Input type="email" value={form.email} onChange={handleField("email")} />
            </Field>
            <Field label="Full name">
              <Input value={form.full_name} onChange={handleField("full_name")} />
            </Field>
            <Field label="Timezone">
              <TimezonePicker
                value={form.timezone}
                onChange={(zone) => setForm((current) => ({ ...current, timezone: zone }))}
              />
            </Field>
            <div className="flex gap-6 pt-1 text-sm">
              <Toggle label="Active" checked={form.is_active} onChange={handleField("is_active")} />
              <Toggle label="Admin" checked={form.is_admin} onChange={handleField("is_admin")} />
            </div>
            <div className="flex justify-between pt-3 border-t">
              <Button variant="outline" size="sm" onClick={() => setResetOpen(true)}>
                Reset password…
              </Button>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
                <Button onClick={submit} disabled={update.isPending}>Save</Button>
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
