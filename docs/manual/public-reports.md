# Public reports

> Traducción: [public-reports.es.md](public-reports.es.md).

Public reports expose a read-only snapshot of a bug, an execution, or the full bug list of a project version to anyone with the URL — no login required. Useful for sharing test results with external stakeholders (PMs, clients, regulators) without giving them an account.

## What can be shared

| Kind | What the viewer sees |
|------|----------------------|
| `bug` | A single bug: title, status, severity, description (markdown rendered), context (version, environment, assignee), and the activity timeline (status changes, comments, attachments) |
| `execution` | A single execution: summary, every result + step result, attached logs, attachments rendered inline as data URLs |
| `bug_report` | The bug list of a project filtered by version: the same release-notes-style HTML you can download from the bugs page |

In v1.0 the supported kinds are fixed to those three. Each kind reuses the same HTML report renderer that powers the in-app **Download HTML** buttons, so the visual is identical.

## Creating a token

On the relevant page (bug detail, execution detail, or project bugs), click **Share** (link icon). The dialog shows:

- **Existing shares** — every token currently active for this resource, with label, created date, and viewer count
- **Create new** — label (free text, only visible to you), optional expiration date

Hit **Generate**. The new token is shown once — copy it now. The URL format is `https://your-instance/public/<short-token>/...`.

The dialog stays open so you can copy the URL or revoke any existing share.

## Tokens and security

- Tokens are opaque 32-character random strings. Anyone with the URL can view the resource — there is no further authentication.
- Tokens are scoped to a single resource. They cannot be used to access any other resource on the instance.
- Tokens are revocable. Click **Revoke** to invalidate immediately — the next request from that URL returns a 410 page styled with the instance app name.
- Tokens optionally expire. Past the expiration the URL returns 410.
- The anonymous viewer is never able to mutate anything (comment, edit, download attachments behind auth) — only read the rendered HTML.

## Branded error page

If the token is revoked, expired, or invalid, the viewer doesn't see a generic 404. The error page carries the instance's app name, locale (based on browser `Accept-Language`), and a contact-the-owner suggestion. The viewer knows the resource existed and was removed, not that they made a typo.

## What's exposed in the HTML

The rendered HTML is **self-contained**:

- Markdown is rendered server-side (no JS execution at the viewer)
- Image attachments are inlined as `data:` URLs (subject to the configured per-instance inline attachment cap)
- Mentions resolve to plain-text labels (anonymous viewers don't see internal user profiles or follow links)
- Custom field values render with their labels and colour chips
- The full activity timeline is included, so the viewer sees the audit trail too

Nothing internal to the instance (URLs to other projects, internal user IDs, JWT tokens) leaks via the rendered page.

## Permissions

| Action | Required role |
|--------|---------------|
| List shares for a resource | viewer / tester / owner / admin |
| Create a share token | tester / owner / admin |
| Revoke a share token | tester / owner / admin |

Project membership is checked at share creation, not at viewer access — once a token exists, anyone with the URL can use it until revoked.

## Audit trail

The list of currently active tokens (with label + creator + creation date) is the audit trail. There's no per-view counter in v1.0; future versions may add view stats.
