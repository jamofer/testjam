# Administration

> Traducción: [admin.es.md](admin.es.md).

This page is meant for the **global admin** of a Testjam instance. Project owners do not need it.

The admin sidebar shows three areas (visible only when `is_admin = true`):

- **Users & Groups** (`/users`) — manage every account on the instance.
- **Settings** (`/settings`) — instance-wide configuration, backups, email defaults.
- (Coming soon) **Projects** — global view across all projects, see [Extended admin](../planned/admin-extended.md).

## Users & Groups

### Users panel

The table lists every user, including deleted ones if **Show deleted** is toggled on.

Operations available per row:

- **Activate / deactivate** — set `is_active`. Inactive users cannot log in but their attribution stays in history.
- **Promote / demote admin** — flips `is_admin`. At least one admin must remain on the instance.
- **Reset password** — opens the same reset flow as the user-facing **Forgot password** link, but it works even when SMTP is misconfigured (a temporary password is shown in a dialog).
- **Delete** — soft-delete. The dialog asks what to do with projects the user owns:

  > _"User Alice owns 3 projects. Reassign each one to another user or archive it."_

  Per project, choose **Reassign → <user>** or **Archive**. Without choosing for at least one owned project, the request returns `409 Conflict`.

- **Restore** — appears on the row of a deleted user. Clears `deleted_at` and reactivates the account.

### Self-delete

Users can request to delete their own account from **Profile → Delete account** only when **Settings → Allow user self-delete** is on. The same owner-reassign rules apply.

### Groups

Groups exist in the data model but are currently unused for permission resolution. The plan is to give them purpose through [Groups with purpose](../planned/groups.md).

## Settings

The settings page is composed of small cards, each editable in place.

### General

- **Site name** — displayed in the browser title and email templates.
- **Site URL** — interpolated into all outgoing links (password reset, notifications). Must be the **public** URL (HTTPS in production).
- **Default user timezone** — applied to new accounts (planned, see [Dates & timezones](../planned/dashboards.md#dates--timezones)).

### Email

- **SMTP host / port / username / password / from**.
- **Test email** button — sends a one-off mail to the requesting admin.

When SMTP is unconfigured, password reset and notification emails are silently skipped and logged at `WARNING`.

### Security

- **Allow user self-delete** — gates the **Profile → Delete account** flow.
- **Account lockout** — number of failed logins and lockout duration in minutes.
- **Password policy** — minimum length and required character classes.

### Backups

Two destructive flows live here. Both are admin-only.

#### Download backup

Generates a ZIP with:

```
manifest.json   — dialect, app version, timestamp, schema head
dump.sql        — pg_dump of the database
uploads/        — the entire attachments tree
```

The dialect (`postgresql` / `sqlite`) is recorded in the manifest. Restoring across dialects is not supported — see warning below.

#### Restore from backup

> **Warning:** Restore is destructive. It drops the existing tables, replays the dump and replaces the entire `uploads/` tree. Existing data is lost permanently.

The form requires:

1. Uploading the ZIP produced by **Download backup**.
2. Typing the literal phrase `REPLACE ALL DATA` to confirm.

The server validates:

- That the ZIP contains `manifest.json` and `dump.sql`.
- That the manifest's `dialect` matches the current server.
- That the manifest's `schema_head` is `<=` the current Alembic head; older schemas are restored as-is and you must run `alembic upgrade head` after.

When in doubt, take a fresh **Download backup** **before** running a restore.

### Periodic backup script

For automated retention, `scripts/backup.sh` (also surfaced as `make backup`) writes a timestamped `testjam-<UTC>.tar.gz` to `BACKUP_DIR` (default `./backups`) and prunes archives older than `RETENTION_DAYS` (default 14). Schedule it from cron or systemd timers.

## Observability

Every instance exposes:

- `GET /health` — JSON with `status`, `version`, `db`.
- `X-Request-ID` header on every response — UUIDv4 for correlation.
- Structured JSON logs with `request_id`, `user_id`, `latency_ms`, `path`, `status`.

If you set `SENTRY_DSN` (backend) and `VITE_SENTRY_DSN` (frontend), errors are forwarded with PII scrubbed and tagged with `request_id` so a log line and a Sentry event correlate.

## API quick reference

| Endpoint                                       | Verb   | Purpose                                |
|------------------------------------------------|--------|----------------------------------------|
| `/api/v1/users`                                | GET    | List users (admin-only).               |
| `/api/v1/users`                                | POST   | Create a user (admin-only).            |
| `/api/v1/users/{id}`                           | PATCH  | Update profile flags.                  |
| `/api/v1/users/{id}`                           | DELETE | Soft-delete with owner-reassign body.  |
| `/api/v1/users/{id}/restore`                   | POST   | Restore a deleted user.                |
| `/api/v1/settings`                             | GET    | Read instance settings.                |
| `/api/v1/settings`                             | PATCH  | Update instance settings.              |
| `/api/v1/admin/backup`                         | GET    | Download a backup ZIP.                 |
| `/api/v1/admin/restore`                        | POST   | Upload + restore a backup ZIP.         |
| `/api/v1/health`                               | GET    | Health endpoint.                       |
