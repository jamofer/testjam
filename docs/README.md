<div align="center">

<img src="logo.svg" width="96" alt="Testjam logo" />

# Testjam — Documentation

</div>

This folder groups every piece of documentation aimed at end-users (QA, developers) and instance administrators. It is split in two blocks:

- **[User manual](manual/README.md)** — features available in the current release.
- **[Architecture](architecture.md)** — backend + frontend project structure, conventions, and data model. Useful for contributors and LLM assistants.
- **[Planned features](planned/README.md)** — skeleton of roadmap items that are **not yet implemented**. Useful to understand where the product is heading and to anticipate integrations.

> Spanish translation: [README.es.md](README.es.md).

**Available UI languages:** English (`en`, default), Spanish (`es`), Catalan (`ca`), Galician (`gl`), Basque (`eu`). Switch under Profile → Appearance → Language. The choice persists on your user, drives both the UI and outgoing notification emails, and falls back to your browser language for new accounts.

---

## Quick navigation

### Manual

| Section | Purpose |
|---------|---------|
| [Getting started](manual/getting-started.md) | Deploy Testjam, create the first admin, sign in. |
| [Projects](manual/projects.md) | Create, archive, export projects. |
| [Dashboard](manual/dashboard.md) | Per-project landing view with metrics, recent runs, open bugs. |
| [Suites & cases](manual/suites-and-cases.md) | Modelling the test library. |
| [Plans](manual/plans.md) | Curate versioned bundles of cases. |
| [Executions](manual/executions.md) | Manual and automatic runs, live view. |
| [Bugs](manual/bugs.md) | Native bug tracker tied to executions and versions. |
| [Mentions](manual/mentions.md) | `@user`, `#bug`, `!run`, `~case` references with notifications. |
| [Versions, environments & coverage](manual/versions-environments-coverage.md) | Per-project release + target organisation. |
| [Custom fields](manual/custom-fields.md) | Extend bugs, cases, executions with structured fields. |
| [Notifications](manual/notifications.md) | In-app bell, email, WebSocket push, per-user preferences. |
| [Public reports](manual/public-reports.md) | Tokenised read-only shares of bugs and executions. |
| [External linking](manual/external-linking.md) | Jira / GitHub / GitLab / Azure DevOps / OpenProject. |
| [Outgoing webhooks](manual/webhooks.md) | HMAC-signed events pushed to external systems. |
| [Import & export](manual/import-export.md) | JUnit, Robot Framework, HTML/PDF/XLSX, project ZIP. |
| [Robot listener](manual/robot-listener.md) | Stream results from your CI. |
| [Python SDK](manual/sdk.md) | `testjam-client` setup, auth, resource modules, CI examples. |
| [`testjam` CLI](manual/cli.md) | Interactive shell + scriptable commands against the API. |
| [Members & API tokens](manual/members-and-tokens.md) | Roles, permissions, `X-API-Key`. |
| [Groups](manual/groups.md) | Bundle users for project access by group. |
| [Appearance](manual/appearance.md) | Dark mode + UI language per user. |
| [Administration](manual/admin.md) | Global users, instance settings, backups. |
| [Keyboard shortcuts](manual/keyboard-shortcuts.md) | Full table of bindings. |

### Planned (not available yet)

| Section | Summary |
|---------|---------|
| [Docker runner](planned/docker-runner.md) | Run automatic tests without an external CI. |
| [Multi-tenant](planned/multi-tenant.md) | Organizations as a layer above projects. |

---

## Reference screenshots

Images used by this manual live in [`screenshots/`](screenshots/README.md). If a capture becomes outdated after a UI change, regenerate the set following the README inside that folder.
