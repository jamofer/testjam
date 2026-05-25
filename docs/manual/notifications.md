# Notifications

> Traducción: [notifications.es.md](notifications.es.md).

Testjam delivers event notifications via three channels — in-app bell, email, and WebSocket push — with per-user, per-event preferences. The same event is rendered consistently across channels and locales.

## Channels

| Channel | Where | Persistence |
|---------|-------|-------------|
| **In-app** | Bell icon in the topbar; clicking opens a paginated list with unread badges | Persisted on `Notification` table; `is_read` flag |
| **Email** | Sent through the SMTP configured in instance Settings | Not persisted by Testjam after send |
| **WebSocket** | Live push to any tab the user has open; the bell badge updates without refresh | In-memory, no persistence |

In-app + WebSocket always fire together for any subscribed event — the WebSocket is just the live channel for the same `Notification` row. Email is opt-in per event.

## Event catalog

| Event | Trigger |
|-------|---------|
| `execution_assigned` | An execution is assigned to me |
| `execution_finished` | An execution I'm assigned to finishes (`completed` or `aborted`) |
| `execution_failed` | An execution I'm assigned to finishes with at least one failed result |
| `bug_assigned` | A bug is assigned to me |
| `bug_commented` | A bug I'm watching receives a comment |
| `bug_status_changed` | A bug I'm watching transitions status |
| `mention_received` | I'm mentioned in any markdown body (`@me`) |
| `password_reset` | I requested a password reset (always sent, not toggleable) |

Test invitations and admin notifications (account deactivated, etc.) are always delivered — not user-toggleable.

## Per-user preferences

**Profile → Notifications** shows a table with one row per event and two checkboxes per row:

- **In-app** — show in the bell + WebSocket push
- **Email** — send through SMTP

Defaults: in-app on for everything; email on for `execution_failed`, `bug_assigned`, `mention_received`, `password_reset`. Adjust to taste.

The locale used for the email subject + body is the recipient's stored `User.locale`, **not** the actor's. So a Spanish-speaking user mentioned by an English-speaking colleague receives the email in Spanish.

## In-app bell

The bell badge shows the unread count. Clicking opens a dropdown / popup with:

- The most recent notifications (paginated; scroll to load older)
- Each row shows the event icon, the localised summary line, the actor name, and the relative timestamp
- Click a row to jump to the source entity and mark the notification read
- **Mark all as read** clears the badge in one click

Notifications older than 90 days are automatically purged by a periodic cleanup job (configurable via `NOTIFICATION_RETENTION_DAYS`).

## WebSocket connection

When you sign in, Testjam opens a single WebSocket per browser tab. The bell badge and notification list update live without a manual refresh. If the connection drops (server restart, network blip), the client reconnects automatically with exponential backoff.

The same WebSocket also carries the live updates that drive the execution-run page, the project bugs page, and the dashboard.

## Email content

Every email follows a localised template per event. The body includes:

- The event summary
- A link back to the source entity (resolved against the configured `site_url`)
- A standard footer naming the instance and a link to the notification preferences page so the recipient can opt out without admin help

If `site_url` is not configured in instance Settings, email-triggering endpoints return `503` rather than sending broken links. See [Administration](admin.md) for the required env vars.

## Permissions

Notification preferences are per-user. There is no admin override in v1.0 — each user controls their own subscriptions. Admins can see the global notification table for debugging via the database; there is no UI for it.
