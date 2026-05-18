import { useState } from "react"
import { useTranslation } from "react-i18next"
import { ExternalLink, Plus, RefreshCw, Trash2 } from "lucide-react"
import { toast } from "sonner"

import {
  useBugExternalLinks,
  useDeleteBugExternalLink,
  useIntegrations,
  usePushBugToIntegration,
  useSyncBugExternalLink,
} from "../../hooks/useIntegrations"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"


export function BugExternalLinksPanel({ bug }) {
  const { t } = useTranslation("integrations")
  const { data: links = [], isLoading } = useBugExternalLinks(bug.id)
  const { data: integrations = [] } = useIntegrations(bug.project_id)
  const push = usePushBugToIntegration(bug.id)
  const sync = useSyncBugExternalLink(bug.id)
  const remove = useDeleteBugExternalLink(bug.id)
  const [selected, setSelected] = useState("")

  const usable = integrations.filter(item => item.is_active && item.has_credential)

  const handlePush = async () => {
    if (!selected) return
    try {
      await push.mutateAsync({ integrationId: Number(selected), labels: [] })
      toast.success(t("bugLinks.pushed"))
      setSelected("")
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("bugLinks.pushFailed"))
    }
  }

  const handleSync = async (linkId) => {
    try {
      await sync.mutateAsync(linkId)
      toast.success(t("bugLinks.synced"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("bugLinks.syncFailed"))
    }
  }

  const handleDelete = async (linkId) => {
    try {
      await remove.mutateAsync(linkId)
      toast.success(t("bugLinks.removed"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("bugLinks.removeFailed"))
    }
  }

  return (
    <div className="space-y-2 text-xs">
      {!isLoading && links.length === 0 && (
        <p className="text-gray-400 dark:text-gray-500">{t("bugLinks.empty")}</p>
      )}
      <ul className="space-y-1.5">
        {links.map(link => (
          <li key={link.id} className="flex items-start gap-2 group">
            <ExternalLink size={11} className="text-gray-400 dark:text-gray-500 mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <a
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 dark:text-primary-400 hover:underline break-words"
              >
                {(link.provider ?? "link")} · {link.external_id || link.url}
              </a>
              <div className="mt-0.5 flex items-center gap-1 flex-wrap">
                <Badge variant={statusVariant(link.status_normalized)}>
                  {t(`bugLinks.status.${link.status_normalized}`)}
                </Badge>
                {link.status_raw && (
                  <span className="text-[11px] text-gray-400 dark:text-gray-500">{link.status_raw}</span>
                )}
              </div>
            </div>
            {link.integration_id != null && (
              <button
                type="button"
                onClick={() => handleSync(link.id)}
                className="text-gray-300 dark:text-gray-600 hover:text-primary-600 opacity-0 group-hover:opacity-100 shrink-0"
                title={t("bugLinks.sync")}
              >
                <RefreshCw size={11} />
              </button>
            )}
            <button
              type="button"
              onClick={() => handleDelete(link.id)}
              className="text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 shrink-0"
              title={t("bugLinks.remove")}
            >
              <Trash2 size={11} />
            </button>
          </li>
        ))}
      </ul>

      {usable.length > 0 ? (
        <div className="flex items-center gap-1 pt-1 border-t border-gray-100 dark:border-gray-800">
          <Select value={selected} onValueChange={setSelected}>
            <SelectTrigger className="h-7 text-[11px] flex-1">
              <SelectValue placeholder={t("bugLinks.pickIntegration")} />
            </SelectTrigger>
            <SelectContent>
              {usable.map(item => (
                <SelectItem key={item.id} value={String(item.id)}>
                  {item.name} ({item.provider})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" variant="outline" onClick={handlePush} disabled={!selected || push.isPending}>
            <Plus size={11} /> {t("bugLinks.push")}
          </Button>
        </div>
      ) : (
        <p className="text-[11px] text-gray-400 dark:text-gray-500">
          {t("bugLinks.noIntegrations")}
        </p>
      )}
    </div>
  )
}


function statusVariant(status) {
  if (status === "open") return "warning"
  if (status === "closed") return "success"
  return "secondary"
}
