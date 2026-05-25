# Executions

> Traducción: [executions.es.md](executions.es.md).

An **execution** is a concrete run of a plan. Each execution carries:

- A `type` — `manual` or `automatic`.
- A `status` — `pending`, `in_progress`, `completed`, `aborted`.
- A snapshot of the plan's cases as **results** (one row per case).
- Each result has its own snapshot of the case's steps as **step results**.

<p align="center">
  <img src="../screenshots/run.png" alt="Execution run page with focused result" width="80%" />
</p>

## Create

From **Project → Executions → New execution** (or the **Run plan** shortcut on a plan):

| Field         | Required | Notes                                                          |
|---------------|----------|----------------------------------------------------------------|
| `plan_id`     | yes      | Pre-filled if launched from the plan page.                     |
| `name`        | yes      | E.g. *Smoke 1.4 — staging*.                                    |
| `type`        | yes      | `manual` for a tester-driven run, `automatic` for CI ingestion. |
| `version_id`  | no       | Defaults to the plan's pinned version.                         |
| `environment` | no       | Free-form label (e.g. `staging`, `prod-eu-1`).                  |
| `assigned_to` | no       | Default tester for the whole run; per-result overrides allowed. |

Hitting **Create** materialises the cases into results with status `not_run`.

## Manual run

Open the execution from `/projects/:id/executions` and click **Run**. The run page (`/executions/:id/run`) is built for speed.

### Keyboard

| Keys                          | Action                                              |
|-------------------------------|-----------------------------------------------------|
| `j` / `k`                     | Next / previous step.                               |
| `↓` / `↑`                     | Same as `j` / `k`.                                  |
| `J` / `K`                     | Next / previous **case** (skip steps).              |
| `h` / `l`                     | Collapse / expand the focused result.               |
| `Home` / `End`                | Jump to first / last result.                        |
| `PageDown` / `PageUp`         | Jump between suites.                                |
| `F` / `B` / `U`               | Jump to next failed / blocked / not-run result.     |
| `p` / `f` / `b` / `n`         | Mark focused result as passed / failed / blocked / not run. |
| `+` / `−`                     | Expand / collapse all results.                      |
| `o`                           | Toggle expand on the focused result.                |
| `L`                           | Toggle "follow live updates".                       |
| `r`                           | Resume follow-live after manual scroll.             |
| `?`                           | Open the shortcut help panel.                       |

Mouse interactions remain available at all times — keyboard is purely additive.

### Per-step inputs

Each step row exposes:

- A status pill (same four states as the result).
- A free-form **notes** field (Markdown).
- **Actual result** — what the tester actually saw.
- An attachments uploader — screenshots, payloads, anything.

### Bulk operations

The action bar at the top of the run page can set status / assignee on every selected result. Selection is per-row checkbox or `Shift+Click` for ranges.

## Automatic execution

When `type = automatic`, the execution is meant to be driven by an external process (CI, the [Robot listener](robot-listener.md), or your own scripts using the REST API). The UI exposes the same view but with mutating keys disabled — you observe rather than drive.

- The `POST /executions/{id}/results/{result_id}` endpoint accepts a partial body, so a CI can stream status + duration + step logs as it runs.
- A live websocket is open at `/api/v1/ws/executions/{id}`. Every status change, log line, or step transition is published as a JSON event. The run page subscribes to it automatically.

## Reports

From an execution detail page the **Export** button offers:

| Format | Notes                                                                                 |
|--------|---------------------------------------------------------------------------------------|
| HTML   | Self-contained. Attachments inlined as base64 data URLs. Email-able.                   |
| PDF    | Renders the HTML through a headless Chromium.                                          |
| XLSX   | One row per result + a summary sheet with pass / fail / block counts per suite.        |

<p align="center">
  <img src="../screenshots/report.png" alt="HTML export" width="60%" />
</p>

## API quick reference

| Endpoint                                          | Verb   | Purpose                                   |
|---------------------------------------------------|--------|-------------------------------------------|
| `/api/v1/projects/{id}/executions`                | GET    | List executions.                          |
| `/api/v1/projects/{id}/executions`                | POST   | Create execution from a plan.             |
| `/api/v1/executions/{id}`                         | GET    | Read execution + results.                 |
| `/api/v1/executions/{id}/abort`                   | POST   | Abort an in-progress execution.           |
| `/api/v1/executions/{id}/results/{result_id}`     | PATCH  | Update one result (status, notes, …).     |
| `/api/v1/results/{result_id}/steps/{step_id}`     | PATCH  | Update one step result.                   |
| `/api/v1/executions/{id}/export?format=html`      | GET    | Download report.                          |
| `/api/v1/ws/executions/{id}`                      | WS     | Subscribe to live events.                 |
