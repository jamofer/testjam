# Suites & cases

> Traducción: [suites-and-cases.es.md](suites-and-cases.es.md).

Suites and cases together form the **test library** of a project. The library is the source of truth — plans and executions only reference it.

## Suite tree

A **suite** is a hierarchical container. A suite may hold:

- Subsuites (any depth — there is no hard cap, but going beyond ~5 levels makes navigation painful).
- Cases.
- Setup / teardown step blocks that run before and after every case in the suite (used by the Robot listener and by readers exporting reports).

### Create

In the project landing page click **+ New suite**. You will be asked for:

- `name` — required.
- `description` — optional Markdown.
- `parent_suite_id` — set automatically when you create from inside a suite.

### Reorder & reparent

Drag the suite by the grip handle on the left of each row. Dropping over another suite **inside** the row reparents; dropping in the empty space between two suites reorders without changing the parent.

### Delete

Deleting a suite is **cascade**: subsuites, cases and steps go with it. The dialog asks for confirmation. Soft-delete on suites is **not** implemented — if you need a recoverable flow, [archive the whole project](projects.md#archive) instead.

## Case

A **case** lives inside a suite and represents one testable behaviour.

<p align="center">
  <img src="../screenshots/run.png" alt="Case in an execution" width="80%" />
</p>

### Fields

| Field            | Type         | Notes                                                         |
|------------------|--------------|---------------------------------------------------------------|
| `name`           | string       | Required. Shown in the tree and execution lists.              |
| `external_id`    | string       | Optional. Stable key used by JUnit/RF importers.              |
| `description`    | markdown     | Full Markdown editor with attachments.                        |
| `preconditions`  | markdown     | Rendered above the steps during a manual run.                 |
| `tags`           | string list  | Free-form. Used for filtering and grouping in reports.        |
| `priority`       | enum         | `low` / `medium` / `high` / `critical`.                       |
| `automation`     | enum         | `manual` / `automatic`. Hints to runners.                     |
| `assigned_to`    | user ref     | Default tester. Overridable per execution.                    |

### Steps

A **step** is an ordered instruction with two columns:

- **Action** — what the tester does.
- **Expected result** — what should happen.

Both columns accept Markdown. Steps can be reordered via drag-and-drop; their `order` is rewritten 1..N atomically by the bulk reorder endpoint.

### Attachments

Each case can carry attachments (screenshots, payloads, sample CSVs). They are inlined as data URLs in HTML exports.

### Revisions

Every meaningful change to a case writes a row in `case_revisions` with a JSON snapshot. The **Recent History** panel on the case page shows:

- Who changed what.
- An expandable diff against the previous revision.
- A filter to hide automated changes (listener / API tokens) and only see human edits.

## API quick reference

| Endpoint                                          | Verb   | Purpose                                    |
|---------------------------------------------------|--------|--------------------------------------------|
| `/api/v1/projects/{id}/suites`                    | GET    | List suites for a project.                 |
| `/api/v1/projects/{id}/suites`                    | POST   | Create suite.                              |
| `/api/v1/suites/{id}`                             | PATCH  | Update suite.                              |
| `/api/v1/suites/{id}`                             | DELETE | Delete suite cascade.                      |
| `/api/v1/projects/{id}/suites/reorder`            | POST   | Bulk reorder/reparent of suites.           |
| `/api/v1/suites/{id}/cases`                       | GET    | List cases inside a suite.                 |
| `/api/v1/suites/{id}/cases`                       | POST   | Create a case in this suite.               |
| `/api/v1/cases/{id}`                              | GET    | Read full case including steps.            |
| `/api/v1/cases/{id}`                              | PATCH  | Update case metadata.                      |
| `/api/v1/cases/{id}/steps`                        | POST   | Append a step.                             |
| `/api/v1/cases/{id}/steps:replace`                | POST   | Atomic delete-all + create-many.           |
| `/api/v1/cases/{id}/steps/reorder`                | POST   | Rewrite step `order` 1..N.                 |
| `/api/v1/cases/{id}/revisions`                    | GET    | List revisions with snapshots.             |
