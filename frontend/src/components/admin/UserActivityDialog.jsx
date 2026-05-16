import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useQuery } from "@tanstack/react-query"

import { usersApi } from "../../api/users"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { DateLabel } from "../ui/date-label"
import { SkeletonText } from "../ui/skeleton"

export function UserActivityDialog({ user, onClose }) {
  const { t } = useTranslation("admin")
  const { data, isPending } = useQuery({
    queryKey: ["user-activity", user.id],
    queryFn: () => usersApi.activity(user.id),
  })

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("users.activity.title", { username: user.username })}</DialogTitle>
        </DialogHeader>
        {isPending ? <SkeletonText lines={6} /> : <Body data={data} />}
      </DialogContent>
    </Dialog>
  )
}

function Body({ data }) {
  const { t } = useTranslation("admin")
  return (
    <div className="space-y-5 text-sm">
      <Section title={t("users.activity.lastLogin")}>
        {data.last_login_at ? (
          <p>
            <DateLabel iso={data.last_login_at} />
            {data.last_login_ip && <span className="ml-2 text-gray-400 dark:text-gray-500">{t("users.activity.lastLoginFrom", { ip: data.last_login_ip })}</span>}
          </p>
        ) : (
          <p className="text-gray-400 dark:text-gray-500">{t("users.activity.neverLoggedIn")}</p>
        )}
      </Section>
      <Section title={t("users.activity.recentExecutions")}>
        <ActivityList items={data.recent_executions} render={renderExecution} emptyLabel={t("users.activity.noExecutions")} />
      </Section>
      <Section title={t("users.activity.recentCases")}>
        <ActivityList items={data.recent_cases} render={renderCase} emptyLabel={t("users.activity.noCases")} />
      </Section>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <h3 className="font-medium text-gray-800 dark:text-gray-100 mb-2">{title}</h3>
      {children}
    </div>
  )
}

function ActivityList({ items, render, emptyLabel }) {
  if (!items?.length) return <p className="text-gray-400 dark:text-gray-500">{emptyLabel}</p>
  return <ul className="divide-y border rounded-md">{items.map(render)}</ul>
}

function renderExecution(item) {
  return (
    <li key={item.id} className="flex items-center justify-between gap-4 px-3 py-2">
      <Link
        to={`/executions/${item.id}/run`}
        className="grow truncate hover:underline"
      >
        {item.title}
      </Link>
      <span className="shrink-0 text-xs text-gray-400 dark:text-gray-500">
        {item.project_name} · {item.status}
      </span>
      <DateLabel iso={item.created_at} className="shrink-0 text-xs text-gray-400 dark:text-gray-500" />
    </li>
  )
}

function renderCase(item) {
  return (
    <li key={item.id} className="flex items-center justify-between gap-4 px-3 py-2">
      <Link
        to={`/projects/${item.project_id}/cases/${item.id}`}
        className="grow truncate hover:underline"
      >
        {item.name}
      </Link>
      <span className="shrink-0 text-xs text-gray-400 dark:text-gray-500">{item.project_name}</span>
      <DateLabel iso={item.created_at} className="shrink-0 text-xs text-gray-400 dark:text-gray-500" />
    </li>
  )
}
