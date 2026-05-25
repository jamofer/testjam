# Project dashboard

> Traducción: [dashboard.es.md](dashboard.es.md).

Each project surface opens on a **Dashboard** tab that summarises the state of the project across a configurable time window (last 7 / 30 / 90 days). The dashboard is read-only — it surfaces what's happening without committing to any deeper page until you click through.

## Widgets

### Project counts

Top-left card. Four stats in a 2×2 grid:

- **Suites** — total suite count
- **Cases** — total case count
- **Plans** — total plan count
- **In flight** — executions currently in `pending` or `in_progress`

### Pass rate

Top-right card. Two parts:

- Overall pass rate across the window, as a percentage. `—` if no results
- A sparkline of daily pass rate over the window

### Recent executions

Lists the last few executions with the *derived* status (not the raw `completed` label):

- `Pass` (green) — completed with no failures and at least one pass
- `Fail` (red) — completed with at least one failed result
- `Blocked` (yellow) — completed with at least one blocked result
- `Aborted` / `In progress` / `Pending` — passed through verbatim
- `Not run` — completed with nothing actually run

A tight chip strip on the right shows `✓P · ✗F · ⚠B · ◦NR` counts so you can see at a glance how the run went. Click any row to jump to the run.

### Top fail-prone cases

Cases sorted by fail count across the window. Useful for finding flaky tests to investigate.

### Open bugs

Cards lists active bugs (`open` / `in_progress`) by severity, plus the 5 most recent ones as clickable links. Sorted by bug number descending so the newest are first. View-all link to the full bugs page.

### Versions

Active versions, each with total runs in the window + pass rate. Color-coded: green ≥80%, yellow ≥50%, red below. Useful for release-readiness gating.

## Range selector

Three buttons at the top: **7d** · **30d** · **90d**. The default is 30 days. Selection is per-page (not persisted across sessions in v1.0).

## Empty state

A fresh project with no executions shows the counts card and the "No executions / No failures / No active versions" empty states in the other widgets — no broken charts, no `NaN%`.

## Refresh and live updates

The dashboard auto-refreshes when you re-enter the page. Live updates from in-flight executions (WebSocket) keep the **In flight** counter accurate without manual refresh.

## Permissions

Any project member (`viewer` and above) can see the dashboard. The data underneath is filtered by project membership, so cross-project values never leak.
