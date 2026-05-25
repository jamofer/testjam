# Bug tracker

> Traducción: [bugs.es.md](bugs.es.md).

Testjam ships a native bug tracker bound to the testing cycle. Defects are born from failed or blocked results with full execution context attached, evolve through a status workflow, and can be cross-linked to external tickets without leaving the app.

## Reporting a bug

From a failed or blocked result in `ExecutionRunPage` or `ExecutionDetailPage`, click **Report bug**. The dialog pre-fills:

- Affected version and environment from the execution
- Severity (default `medium`) and tags
- Description, with the failed step's log attached automatically
- Optional link back to the result / execution

Bugs can also be created manually from the project **Bugs** page (**New bug** button) without a backing result.

## Status workflow

| Status | Meaning |
|--------|---------|
| `open` | Reported, not yet picked up |
| `in_progress` | Under investigation or being fixed |
| `resolved` | Fix landed, awaiting verification |
| `closed` | Verified and shipped |
| `wont_fix` | Acknowledged, intentionally not fixed |
| `not_a_bug` | Triaged as non-defect |

Transitions are tracked in the activity timeline with the actor, timestamp, and optional note.

## Severity

`critical` · `high` · `medium` · `low`. Visualised as a pill on every row and on the detail page. Custom fields can layer extra dimensions (priority, business impact, target version) — see [Custom fields](custom-fields.md).

## Bug detail

The detail page groups:

- **Header**: title, severity badge, status pill, watch toggle, delete (owner/admin only)
- **Description**: markdown editor with inline preview
- **Comments**: threaded markdown comments, edit with inline diff in the activity timeline
- **Attachments**: drag-and-drop upload, copy MD link, authenticated download. Size cap + MIME deny-list enforced server-side (no HTML / SVG / executables)
- **Activity timeline**: status changes, field edits, comments, attachments, link add/remove, custom field diffs — every actor + timestamp
- **Context panel** (right side): assignee, affected version, fixed-in version, environment, watchers, linked results / executions, external tracker links, custom fields

## Watchers

Click **Watch** to get notifications on status changes, comments, and assignee updates. The reporter and the assignee are auto-watched. Watchers list visible to project members; user can unwatch any time.

## Mentions

Type `@user` to mention any project member (email + in-app notification). `#bug-number`, `!execution-id`, `~case-id` chips render as breadcrumb pills with title + status. See [Mentions](mentions.md) for the full grammar.

## External linking

A bug can be linked to one or more external trackers (Jira, GitHub Issues, GitLab Issues, Azure DevOps Work Items, OpenProject). Linking is **push-on-demand** + **pull-on-demand** in v1.0 (no background sync). See [External linking](external-linking.md).

## Filters and search

The bug list supports filtering by status, severity, version, custom field, free-text search (title), and tags. Filters are persisted in the URL — refresh or share keeps the filtered view intact.

Bulk actions are not in v1.0; planned for v1.1.

## Release notes

**Project → Bugs → Release notes** generates a printable HTML report grouped by `fixed_in_version`, with the bug title, severity, and resolution date. Useful as a release changelog. Available via the same endpoint that the public-report token can expose externally.

## Public sharing

Generate a tokenised read-only URL for a bug or for the full bug list of a version. See [Public reports](public-reports.md).

## Permissions

| Action | Required role |
|--------|---------------|
| View bugs | viewer / tester / owner / admin |
| Create, edit, comment, change status | tester / owner / admin |
| Delete bug, delete any user's comment | owner / admin |
| Delete own comment | author |

Viewers see the read-only surface; destructive buttons are hidden in the UI to avoid 403 toasts.
