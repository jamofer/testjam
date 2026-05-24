// Derive the current user's effective role on a project from cached
// `useMe` + `useMembers` data. Provides the two role booleans every
// destructive button in the project surface should respect:
//
//   canWrite  → owner / tester / admin (covers create/edit/link/comment
//               delete and anything `_require_writer` gates server-side)
//   canDelete → owner / admin (matches the backend's
//               `_can_delete_project_resource`, used for bug / project
//               deletes that are owner-only)
//
// Returns conservative defaults (everything false) while data is still
// loading so we never flash a destructive button to a viewer.

import { useMe } from "./useAuth"
import { useMembers } from "./useMembers"

const WRITER_ROLES = new Set(["owner", "tester"])

export function useProjectRole(projectId) {
  const { data: me } = useMe()
  const { data: members = [], isLoading } = useMembers(projectId)

  if (!projectId || !me) {
    return { role: null, canWrite: false, canDelete: false, isLoading: !!projectId && (!me || isLoading) }
  }
  if (me.is_admin) {
    return { role: "admin", canWrite: true, canDelete: true, isLoading: false }
  }
  const membership = members.find(member => member.user_id === me.id)
  const role = membership?.role ?? null
  return {
    role,
    canWrite: WRITER_ROLES.has(role),
    canDelete: role === "owner",
    isLoading,
  }
}
