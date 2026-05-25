# Projects

> Traducción: [projects.es.md](projects.es.md).

A **project** is the top-level container in Testjam. Everything else — suites, cases, plans, executions, members, tokens — lives inside one.

<p align="center">
  <img src="../screenshots/suites.png" alt="Project detail with nested suites" width="80%" />
</p>

## Create

From `/projects` click **New project**.

| Field         | Required | Notes                                                              |
|---------------|----------|--------------------------------------------------------------------|
| `name`        | yes      | Free-form. Displayed in the sidebar and breadcrumbs.               |
| `slug`        | no       | Generated automatically from `name` if you leave it empty.         |
| `description` | no       | Markdown supported, rendered on the project landing page.          |

The user that creates the project becomes its **owner**. Owners can add members later from [Members & API tokens](members-and-tokens.md).

## Project landing page

The landing page (`/projects/:id`) renders:

- A breadcrumb header with the project name and quick links.
- The hierarchical tree of **suites** + **cases**.
- An action bar to create new top-level suites or top-level cases.
- A keyboard hint reminding you of `?` to open the shortcut panel.

The suites tree supports:

- Drag-and-drop reordering and reparenting.
- `+` / `−` to expand/collapse all.
- `/` to focus the search input.
- `Home` / `End` to jump to first/last treeitem.
- `PageUp` / `PageDown` to jump between sibling suites.

## Archive

Use **Project → Settings → Archive project** to mark the project read-only without losing data. While archived:

- Every mutating endpoint returns `409 Conflict` with `detail = "Project is archived"`.
- The project is hidden from the default `GET /projects` listing.
- Pass `?include_archived=true` to surface it again.

You can unarchive at any time from the same settings page or via `POST /projects/{id}/unarchive`.

Archive is the recommended way to retire stale projects — it preserves history for audits and exports.

## Delete

Hard-deleting a project is only available to global admins from **Admin → Projects** (this view is part of the [Extended admin](../planned/admin-extended.md) roadmap and is **not yet wired** in the UI). Until then, archive is the supported flow.

## Export

The project header has an **Export** button (owner / editor / admin). It builds a deterministic ZIP named `project-<slug>-<UTC>.zip` containing:

```
manifest.json        – format version + project metadata
project.json         – suites, cases, steps, plans (JSON dump)
attachments/         – binary case & result attachments
```

The export is useful for:

- Migrating a project between instances.
- Long-term archival before deleting.
- Reproducing a bug — attach the ZIP to an issue.

Importing the ZIP back into another Testjam instance is supported from `POST /projects/import`.

## API quick reference

| Endpoint                                       | Verb   | Purpose                                |
|------------------------------------------------|--------|----------------------------------------|
| `/api/v1/projects`                             | GET    | List visible projects.                 |
| `/api/v1/projects`                             | POST   | Create a project.                      |
| `/api/v1/projects/{id}`                        | GET    | Read project metadata.                 |
| `/api/v1/projects/{id}`                        | PATCH  | Update name, slug, description.        |
| `/api/v1/projects/{id}/archive`                | POST   | Archive (read-only).                   |
| `/api/v1/projects/{id}/unarchive`              | POST   | Restore from archive.                  |
| `/api/v1/projects/{id}/export`                 | GET    | Download project ZIP.                  |
| `/api/v1/projects/import`                      | POST   | Import a project ZIP.                  |
