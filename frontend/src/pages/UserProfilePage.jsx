import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { User as UserIcon, Globe, Calendar, Shield, Clock } from "lucide-react"

import { usersApi } from "../api/users"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Badge } from "../components/ui/badge"
import { SkeletonList } from "../components/ui/skeleton"
import { EmptyState } from "../components/ui/empty-state"
import { DateLabel } from "../components/ui/date-label"

export function UserProfilePage() {
  const { t } = useTranslation(["profile", "nav"])
  const { username } = useParams()
  const { data: user, isLoading, isError } = useQuery({
    queryKey: ["user-profile", username],
    queryFn: () => usersApi.getByUsername(username),
    enabled: !!username,
    retry: false,
  })

  return (
    <>
      <PageHeader crumbs={[
        { label: t("nav:global.users"), to: "/users" },
        { label: username },
      ]}>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
          <UserIcon size={20} /> {user?.full_name ?? username}
        </h1>
      </PageHeader>

      <PageBody>
        {isLoading && <SkeletonList count={2} />}
        {isError && (
          <EmptyState
            icon={UserIcon}
            title={t("public.notFoundTitle")}
            description={t("public.notFoundDescription", { username })}
            compact
          />
        )}
        {user && (
          <div className="max-w-xl rounded-xl border bg-white dark:bg-gray-900 p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-500 dark:text-gray-400">@{user.username}</span>
              {user.is_admin && <Badge variant="secondary"><Shield size={11} className="mr-1" /> {t("public.admin")}</Badge>}
              {!user.is_active && <Badge variant="outline">{t("public.inactive")}</Badge>}
              {user.deleted_at && <Badge variant="outline">{t("public.deleted")}</Badge>}
            </div>
            {user.full_name && (
              <p className="text-base text-gray-800 dark:text-gray-100">{user.full_name}</p>
            )}
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <ProfileField icon={Globe} label={t("public.locale")} value={user.locale ?? "—"} />
              <ProfileField icon={Calendar} label={t("public.joined")} value={<DateLabel iso={user.created_at} />} />
              {user.last_login_at && (
                <ProfileField icon={Clock} label={t("public.lastLogin")} value={<DateLabel iso={user.last_login_at} />} />
              )}
            </dl>
          </div>
        )}
      </PageBody>
    </>
  )
}

function ProfileField({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-2">
      <Icon size={13} className="mt-1 text-gray-400 dark:text-gray-500 shrink-0" />
      <div className="min-w-0">
        <dt className="text-xs text-gray-500 dark:text-gray-400">{label}</dt>
        <dd className="text-sm text-gray-800 dark:text-gray-100 break-words">{value}</dd>
      </div>
    </div>
  )
}
