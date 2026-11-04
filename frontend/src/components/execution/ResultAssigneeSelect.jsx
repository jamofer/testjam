import { useTranslation } from "react-i18next"

import { useUpdateResult } from "../../hooks/useExecutions"
import { useMembers } from "../../hooks/useMembers"
import { toastApiError } from "../../lib/apiError"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"

const UNASSIGNED = "__none__"

export function ResultAssigneeSelect({ result, executionId, projectId }) {
  const { t } = useTranslation("executions")
  const { data: members = [] } = useMembers(projectId)
  const updateResult = useUpdateResult(executionId)

  const assign = value => {
    const assignedToId = value === UNASSIGNED ? null : Number(value)
    updateResult.mutate(
      { id: result.id, data: { assigned_to_id: assignedToId } },
      { onError: error => toastApiError(error, t("assignee.failed")) },
    )
  }

  return (
    <Select value={result.assigned_to_id ? String(result.assigned_to_id) : UNASSIGNED} onValueChange={assign}>
      <SelectTrigger className="h-8 w-48 text-xs" aria-label={t("assignee.label")}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={UNASSIGNED}>{t("assignee.unassigned")}</SelectItem>
        {members.map(member => (
          <SelectItem key={member.user_id} value={String(member.user_id)}>{member.username}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export function useAssigneeName(projectId, assignedToId) {
  const { data: members = [] } = useMembers(projectId)
  return members.find(member => member.user_id === assignedToId)?.username ?? null
}
