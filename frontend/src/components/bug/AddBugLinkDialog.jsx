import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { useAddBugLink, useBugs } from "../../hooks/useBugs"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"

export function AddBugLinkDialog({ bugId, projectId, trigger }) {
  const { t } = useTranslation("bugs")
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState("url")
  const [url, setUrl] = useState("")
  const [label, setLabel] = useState("")
  const [targetBugId, setTargetBugId] = useState("")
  const [kind, setKind] = useState("relates_to")
  const addLink = useAddBugLink()
  const { data: bugs = [] } = useBugs(projectId, {})

  const reset = () => {
    setUrl("")
    setLabel("")
    setTargetBugId("")
    setKind("relates_to")
    setTab("url")
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    try {
      const payload = tab === "url"
        ? { url: url.trim(), label: label.trim() || null }
        : { target_bug_id: Number(targetBugId), kind, label: label.trim() || null }
      if (tab === "url" && !payload.url) return
      if (tab === "bug" && !payload.target_bug_id) return
      await addLink.mutateAsync({ id: bugId, data: payload })
      toast.success(t("links.added"))
      setOpen(false)
      reset()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const otherBugs = bugs.filter(bug => bug.id !== bugId)

  return (
    <Dialog open={open} onOpenChange={(next) => { setOpen(next); if (!next) reset() }}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>{t("links.dialogTitle")}</DialogTitle></DialogHeader>
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="url">{t("links.tabUrl")}</TabsTrigger>
            <TabsTrigger value="bug">{t("links.tabBug")}</TabsTrigger>
          </TabsList>
          <form className="space-y-3 mt-3" onSubmit={handleSubmit}>
            <TabsContent value="url" className="space-y-3 mt-0">
              <div className="space-y-1">
                <Label>{t("links.url")}</Label>
                <Input
                  value={url}
                  onChange={event => setUrl(event.target.value)}
                  placeholder="https://…"
                  autoFocus
                />
              </div>
            </TabsContent>
            <TabsContent value="bug" className="space-y-3 mt-0">
              <div className="space-y-1">
                <Label>{t("links.kind")}</Label>
                <Select value={kind} onValueChange={setKind}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {["relates_to", "blocks", "blocked_by", "duplicate_of"].map(value => (
                      <SelectItem key={value} value={value}>
                        {t(`links.kinds.${value}`)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>{t("links.targetBug")}</Label>
                <Select value={targetBugId} onValueChange={setTargetBugId}>
                  <SelectTrigger>
                    <SelectValue placeholder={t("links.targetBugPlaceholder")} />
                  </SelectTrigger>
                  <SelectContent>
                    {otherBugs.map(bug => (
                      <SelectItem key={bug.id} value={String(bug.id)}>
                        #{bug.number} · {bug.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>
            <div className="space-y-1">
              <Label>{t("links.label")}</Label>
              <Input
                value={label}
                onChange={event => setLabel(event.target.value)}
                placeholder={t("links.labelPlaceholder")}
              />
            </div>
            <Button type="submit" className="w-full" disabled={addLink.isPending}>
              {t("actions.save")}
            </Button>
          </form>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
