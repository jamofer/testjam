# Import & export

> Traducción: [import-export.es.md](import-export.es.md).

Testjam ships first-class support to ingest results from existing CI pipelines and to push reports out to humans.

## Importing results

Two formats are supported out of the box:

| Format            | Endpoint                                                | Detection |
|-------------------|---------------------------------------------------------|-----------|
| JUnit XML         | `POST /api/v1/executions/{id}/import?format=junit`      | `<testsuite>` / `<testcase>` |
| Robot Framework   | `POST /api/v1/executions/{id}/import?format=robot`      | `output.xml` from `robot` runs |

Both endpoints expect an in-progress `automatic` execution. The import:

1. Walks the report file and extracts each test case.
2. Matches each one against the execution's results, using `external_id` first, then exact `name`.
3. Updates the matching result with status, duration, error message and per-step logs.
4. Leaves unmatched tests as warnings in the response payload — they are **not** silently created.

### Strategy: stable external IDs

The matcher is happy when every case carries a stable `external_id` that the CI also emits. For Robot, that maps to `[Tags]` `id:<value>`. For JUnit, that maps to the test classname or `name` attribute — pick one and stick to it.

If your suite is small and names are unique, name-based matching is enough. As the suite grows, missing external IDs lead to false negatives on rename.

## Reports out

The execution detail page offers three formats:

- **HTML** — single self-contained file. Attachments are inlined as base64 data URLs, so the file is portable but heavy (a 20 MB report is common with screenshots).
- **PDF** — same HTML rendered through headless Chromium. Slower; intended for printable archival.
- **XLSX** — flat table plus per-suite pivot. Best for spreadsheet pivots and management dashboards.

Reports include the execution metadata header, results table, per-result step breakdown, and a footer with `generated_at` + the user that triggered the export.

## Project ZIP export

A full **project** export ships from the project header (covered in [Projects → Export](projects.md#export)). It contains the test library, plans and selected execution attachments, useful for moving a project between instances.

## Instance backup

The instance-wide **Download backup** / **Restore from backup** flow under **Admin → Settings** is documented in [Administration → Backups](admin.md#backups). It captures the database dump plus the entire `uploads/` tree.

## API quick reference

| Endpoint                                              | Verb   | Purpose                              |
|-------------------------------------------------------|--------|--------------------------------------|
| `/api/v1/executions/{id}/import?format=junit`         | POST   | Ingest JUnit XML.                    |
| `/api/v1/executions/{id}/import?format=robot`         | POST   | Ingest Robot `output.xml`.           |
| `/api/v1/executions/{id}/export?format=html`          | GET    | Download HTML report.                |
| `/api/v1/executions/{id}/export?format=pdf`           | GET    | Download PDF report.                 |
| `/api/v1/executions/{id}/export?format=xlsx`          | GET    | Download XLSX report.                |
| `/api/v1/projects/{id}/export`                        | GET    | Download project ZIP.                |
| `/api/v1/projects/import`                             | POST   | Import a project ZIP.                |
