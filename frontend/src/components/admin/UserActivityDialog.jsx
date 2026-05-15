import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { usersApi } from "../../api/users"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { DateLabel } from "../ui/date-label"
import { SkeletonText } from "../ui/skeleton"

export function UserActivityDialog({ user, onClose }) {
  const { data, isPending } = useQuery({
    queryKey: ["user-activity", user.id],
    queryFn: () => usersApi.activity(user.id),
  })

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Activity — {user.username}</DialogTitle>
        </DialogHeader>
        {isPending ? <SkeletonText lines={6} /> : <Body data={data} />}
      </DialogContent>
    </Dialog>
  )
}

function Body({ data }) {
  return (
    <div className="space-y-5 text-sm">
      <Section title="Last login">
        {data.last_login_at ? (
          <p>
            <DateLabel iso={data.last_login_at} />
            {data.last_login_ip && <span className="ml-2 text-gray-400">from {data.last_login_ip}</span>}
          </p>
        ) : (
          <p className="text-gray-400">Never logged in.</p>
        )}
      </Section>
      <Section title="Recent executions">
        <ActivityList items={data.recent_executions} render={renderExecution} emptyLabel="No executions started yet." />
      </Section>
      <Section title="Recent cases">
        <ActivityList items={data.recent_cases} render={renderCase} emptyLabel="No cases authored yet." />
      </Section>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <h3 className="font-medium text-gray-800 mb-2">{title}</h3>
      {children}
    </div>
  )
}

function ActivityList({ items, render, emptyLabel }) {
  if (!items?.length) return <p className="text-gray-400">{emptyLabel}</p>
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
      <span className="shrink-0 text-xs text-gray-400">
        {item.project_name} · {item.status}
      </span>
      <DateLabel iso={item.created_at} className="shrink-0 text-xs text-gray-400" />
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
      <span className="shrink-0 text-xs text-gray-400">{item.project_name}</span>
      <DateLabel iso={item.created_at} className="shrink-0 text-xs text-gray-400" />
    </li>
  )
}
