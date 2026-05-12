import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { UserPlus, Trash2, Users, Shield } from "lucide-react"
import { api } from "../api/client"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Badge } from "../components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"
import { toast } from "sonner"

const usersApi = {
  list: () => api.get("/users").then(r => r.data),
  create: (data) => api.post("/users", data).then(r => r.data),
  delete: (id) => api.delete(`/users/${id}`),
}

const groupsApi = {
  list: () => api.get("/groups").then(r => r.data),
  create: (data) => api.post("/groups", data).then(r => r.data),
  delete: (id) => api.delete(`/groups/${id}`),
  addMember: (groupId, userId, role) => api.post(`/groups/${groupId}/members`, null, { params: { user_id: userId, role } }),
  removeMember: (groupId, userId) => api.delete(`/groups/${groupId}/members/${userId}`),
}

function CreateUserDialog() {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ username: "", email: "", password: "", full_name: "" })
  const qc = useQueryClient()

  const create = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] })
      toast.success("User created")
      setOpen(false)
      setForm({ username: "", email: "", password: "", full_name: "" })
    },
    onError: () => toast.error("Failed to create user"),
  })

  const field = (key) => ({ value: form[key], onChange: e => setForm(f => ({ ...f, [key]: e.target.value })) })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><UserPlus size={14} /> New user</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Create user</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>Username *</Label><Input {...field("username")} /></div>
          <div className="space-y-1"><Label>Email *</Label><Input type="email" {...field("email")} /></div>
          <div className="space-y-1"><Label>Full name</Label><Input {...field("full_name")} /></div>
          <div className="space-y-1"><Label>Password *</Label><Input type="password" {...field("password")} /></div>
          <Button className="w-full" onClick={() => create.mutate(form)} disabled={create.isPending}>
            Create
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function CreateGroupDialog() {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const qc = useQueryClient()

  const create = useMutation({
    mutationFn: groupsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["groups"] })
      toast.success("Group created")
      setOpen(false)
      setName("")
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline"><Shield size={14} /> New group</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Create group</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label>Name *</Label>
            <Input value={name} onChange={e => setName(e.target.value)} /></div>
          <Button className="w-full" onClick={() => create.mutate({ name })} disabled={!name.trim()}>
            Create
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function UsersPage() {
  const qc = useQueryClient()
  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: usersApi.list })
  const { data: groups = [] } = useQuery({ queryKey: ["groups"], queryFn: groupsApi.list })

  const deleteUser = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("User deleted") },
  })

  const deleteGroup = useMutation({
    mutationFn: groupsApi.delete,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["groups"] }); toast.success("Group deleted") },
  })

  return (
    <div className="pl-14 pr-4 py-4 md:p-8 max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Users & Groups</h1>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users"><Users size={13} className="mr-1" /> Users ({users.length})</TabsTrigger>
          <TabsTrigger value="groups"><Shield size={13} className="mr-1" /> Groups ({groups.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <div className="flex justify-end mb-3"><CreateUserDialog /></div>
          <ul className="space-y-2">
            {users.map(u => (
              <li key={u.id} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3 shadow-sm">
                <div>
                  <p className="font-medium text-gray-800">{u.username}</p>
                  <p className="text-xs text-gray-400">{u.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={u.is_active ? "success" : "secondary"}>{u.is_active ? "active" : "inactive"}</Badge>
                  <Button size="icon" variant="ghost" onClick={() => deleteUser.mutate(u.id)}>
                    <Trash2 size={14} />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </TabsContent>

        <TabsContent value="groups">
          <div className="flex justify-end mb-3"><CreateGroupDialog /></div>
          <ul className="space-y-2">
            {groups.map(g => (
              <li key={g.id} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3 shadow-sm">
                <div>
                  <p className="font-medium text-gray-800">{g.name}</p>
                  <p className="text-xs text-gray-400">{g.members?.length ?? 0} members</p>
                </div>
                <Button size="icon" variant="ghost" onClick={() => deleteGroup.mutate(g.id)}>
                  <Trash2 size={14} />
                </Button>
              </li>
            ))}
          </ul>
        </TabsContent>
      </Tabs>
    </div>
  )
}
