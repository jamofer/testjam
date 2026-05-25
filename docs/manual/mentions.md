# Mentions

> Traducción: [mentions.es.md](mentions.es.md).

Mentions are cross-entity references that resolve to enriched chips (title + status + link) wherever markdown is rendered: bug descriptions, comments, case discussions, public reports, HTML reports. They also fan out as notifications + emails to the targeted users.

## Syntax

| Pattern | Target | Example | Renders as |
|---------|--------|---------|------------|
| `@username` | A user | `@alice` | pill `@alice` linking to the user profile |
| `#N` | A bug in the current project, by number | `#42` | pill `#42 Login broken` |
| `!N` | An execution in the current project, by id | `!100` | pill `!100 Nightly run` |
| `!N/M` | A result inside an execution | `!100/12` | breadcrumb `Nightly run › Login flow` |
| `!N/M/S` | A step result inside a result | `!100/12/3` | breadcrumb `Nightly run › Login flow › Enter password` |
| `~N` | A test case by id | `~57` | pill `~57 Login flow` |

Mentions are parsed in markdown bodies, ignoring fenced or inline code blocks so `\`#42\`` or fenced `!100` stay verbatim.

## Resolver behaviour

When the page renders, each mention is resolved server-side:

- **Found + member can access** → chip with the entity title + status, link to the detail page
- **Found + member can't access** (foreign project, soft-deleted user) → degrades to plain text of the raw token (`#42`, `@alice`) — no information leak
- **Not found** → degrades to plain text

Resolution happens in a single batched call per render, not per occurrence — large reports with hundreds of mentions stay fast.

## Autocomplete

In any markdown editor (bug description, comment, case description, case comment), typing one of the trigger characters opens a Floating UI dropdown with up to 10 matches:

- `@` → users that are project members + admins, ranked by name match
- `#` → bugs in the current project, by number or title substring
- `!` → executions in the current project, by id or title substring
- `~` → cases in the current project, by id or name substring

Selection inserts the canonical token (`@alice`, `#42`, `!100/12`).

## Notifications

When you publish a markdown body containing a `@user` mention, Testjam fans out:

- An **in-app notification** to each mentioned user (visible from the bell in the topbar)
- An **email** to each user that has the `mention_received` event toggled on in their profile preferences

Only `@user` mentions notify. `#bug` / `!run` / `~case` mentions render as chips but do not notify the bug / execution / case watchers (those flows have their own notification triggers).

The fan-out is **strict member-only**: mentions to users that aren't members of the project (or admins) render the chip but skip the notification — no cross-project leakage.

## Edit semantics

When a body is edited, the diff between old and new mentions decides who gets notified:

- New mentions added → notify
- Mentions removed → no notification
- Mentions unchanged → no re-notification (no spam on whitespace edits)

## Public reports

Mentions render as chips in the public HTML report served via the token URL. Only project members see the full enrichment; the anonymous viewer sees the visible label without follow-up links. See [Public reports](public-reports.md).

## Where mentions appear

| Surface | Parsing | Notifications |
|---------|---------|---------------|
| Bug description / comments | yes | yes (users) |
| Test case description / comments | yes | yes (users) |
| Execution / result comments | yes | yes (users) |
| HTML report (bug list) | yes | n/a (render only) |
| Public reports | yes | n/a (render only) |

## Permissions

Anyone with write access to a surface can publish a mention. The resolver respects the viewer's permissions — viewers who lack project access see the chip degrade to plain text instead of a working link.
