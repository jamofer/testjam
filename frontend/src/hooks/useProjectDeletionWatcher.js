import { useMemo } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { useTopicSocket } from "./useTopicSocket"

export function useProjectDeletionWatcher() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { t } = useTranslation("projects")

  const projectId = useMemo(() => extractProjectId(pathname), [pathname])

  const topics = useMemo(
    () => (projectId ? [`project:${projectId}`] : []),
    [projectId],
  )

  const handlers = useMemo(() => ({
    "project.deleted": (data) => {
      if (!data?.id || String(data.id) !== String(projectId)) return
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      navigate("/projects", { replace: true })
      toast.warning(t("deletedRemotely", { name: data.name || "" }))
    },
  }), [queryClient, navigate, projectId, t])

  useTopicSocket(topics, handlers, { enabled: !!projectId })
}

function extractProjectId(pathname) {
  const match = pathname.match(/^\/projects\/(\d+)(?:\/|$)/)
  return match ? match[1] : null
}
