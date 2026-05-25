# Versions, environments, and coverage

> Traducción: [versions-environments-coverage.es.md](versions-environments-coverage.es.md).

Three project-scoped catalogs that organise executions and bugs by where + when the tests ran.

## Versions

A version represents a release candidate, a sprint, a build number — whatever you ship. Bugs are tagged with the version they were detected on (`version_id`) and the version they were fixed in (`fixed_in_version_id`). Executions are tagged with the version under test.

**Project → Versions** lists every version with:

- **Name** — free text, must be unique per project
- **Status** — `active` (default) or `released`
- **VCS tag** — optional, links to a git tag for traceability
- **Release date** — optional, used in release notes
- **Attachments** — release notes PDFs, change logs, etc. (subject to upload size + MIME limits — see [Administration](admin.md))

`released` versions are surfaced first in the bugs filter; `active` versions live above them. Switching a version to `released` stamps `released_at` automatically.

### Editing and deleting

Rename or change the status from the version row. Deletion is blocked while bugs or executions reference the version — archive it or migrate the references first. Versions cannot be undeleted; restore from a backup if you destroyed one by mistake.

### In release notes

Bugs filter `fixed_in_version_id == <version>` powers the **Release notes** report on the bugs page — see [Bugs](bugs.md#release-notes).

## Environments

An environment names a target where you run tests: `staging`, `prod-eu`, `chrome-canary`, etc. Environments live per project and live in the project Settings → Environments panel.

When an execution is created, you can pick from the catalog or type a free-text value. Free-text values are auto-added to the catalog if not present (the so-called *upsert*) so the next run can pick the same string from the dropdown. Bugs reported from a result inherit the environment from the execution.

The environment is rendered as a coloured pill on the bug list, the bug detail context panel, and the execution detail. Colours are stable per slug (hashed) so the same environment looks the same across all pages.

## Coverage matrix

**Project → Coverage** renders a 2-axis matrix of `versions × environments`. Each cell shows the last execution that ran the active plan on that combination, with its pass-rate badge.

| | staging | prod-eu | chrome-canary |
|---|---|---|---|
| **v1.0** | 95% (12/13) | 100% (13/13) | — |
| **v1.1-rc1** | 80% (10/13) | 70% (9/13) | 92% (12/13) |

Useful as a release-readiness gate: a row with green badges across every environment is shippable; a row with `—` cells or red badges flags missing coverage.

Click any cell to jump to that execution.

## Permissions

| Action | Required role |
|--------|---------------|
| List versions / environments / coverage | viewer / tester / owner / admin |
| Create / edit version | tester / owner / admin |
| Delete version | owner / admin |
| Add / remove environment from catalog | tester / owner / admin |

## Notes

- Versions are project-scoped — there is no global version registry. Use a consistent naming convention if you want to track the same release across many projects.
- The coverage matrix uses the latest **completed** execution per (version, environment, plan) tuple. In-flight runs don't populate cells.
- Free-text environment values are normalised (trimmed, lowercased for matching) before being upserted to the catalog so `Staging` and ` staging ` resolve to the same entry.
