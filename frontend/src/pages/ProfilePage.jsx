import { useState, useEffect } from "react"
import { useMe, useUpdateMe, useChangePassword } from "../hooks/useAuth"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { toast } from "sonner"

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
    <div className="max-w-lg space-y-8">
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
