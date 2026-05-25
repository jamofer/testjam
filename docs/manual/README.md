# User manual

Complete guide for end-users (QA, developers) and instance administrators. It only covers what is shipping today — future features live under [`../planned/`](../planned/README.md).

> Traducción: [README.es.md](README.es.md).

<p align="center">
  <img src="../screenshots/hero.png" alt="Testjam — overview" width="80%" />
</p>

## Suggested path

If Testjam is new to you, walk the sections in this order:

1. **[Getting started](getting-started.md)** — install and sign in for the first time.
2. **[Projects](projects.md)** — create the top-level container for your work.
3. **[Dashboard](dashboard.md)** — the per-project landing view.
4. **[Suites & cases](suites-and-cases.md)** — build the test library.
5. **[Plans](plans.md)** — group cases for a particular release.
6. **[Executions](executions.md)** — run a plan manually or from CI.
7. **[Bugs](bugs.md)** — native bug tracker bound to the testing cycle.
8. **[Mentions](mentions.md)** — cross-entity references that resolve to chips and notify users.
9. **[Versions, environments & coverage](versions-environments-coverage.md)** — organise runs by where + when.
10. **[Custom fields](custom-fields.md)** — extend bugs, cases and executions with structured fields.
11. **[Notifications](notifications.md)** — in-app bell, email, WebSocket push, per-user preferences.
12. **[Public reports](public-reports.md)** — tokenised read-only shares of bugs and executions.
13. **[External linking](external-linking.md)** — Jira, GitHub, GitLab, Azure DevOps, OpenProject.
14. **[Outgoing webhooks](webhooks.md)** — HMAC-signed events to external systems.
15. **[Import & export](import-export.md)** — get data in and out.
16. **[Robot listener](robot-listener.md)** — automate ingestion from Robot Framework.
17. **[`testjam` CLI](cli.md)** — interactive shell + scriptable commands against the API.
18. **[Members & API tokens](members-and-tokens.md)** — collaborate with your team.
19. **[Groups](groups.md)** — bundle users so project access can be granted by group.
20. **[Appearance](appearance.md)** — dark mode + UI language per user.
21. **[Administration](admin.md)** — only if you operate the instance.
22. **[Keyboard shortcuts](keyboard-shortcuts.md)** — squeeze the productivity.

## Core concepts

```
Project
 ├── Suite (may nest more suites)
 │    └── Case
 │         └── Step
 ├── Plan (references many cases, M2M)
 ├── Execution
 │    └── Result (one per executed case)
 │         └── Step result
 └── Bug (linked to results, versions, environments)
```

- A **suite** is hierarchical and may hold subsuites in addition to cases.
- A **plan** is a curated collection of cases pinned to a version.
- An **execution** materialises a plan as a concrete run (`manual` or `automatic`).
- **Results** and **step results** share four states: `not_run`, `passed`, `failed`, `blocked`.
- A **bug** is born from a failed or blocked result (or manually) and lives through its own status workflow.

## Roles & permissions at a glance

| Role             | Scope    | Actions                                                |
|------------------|----------|--------------------------------------------------------|
| Global `admin`   | Instance | Everything below + users + settings + backup.         |
| Project `owner`  | 1 project| Project settings, members, archive, delete.            |
| Project `tester` | 1 project| Create/edit/delete suites, cases, plans, executions, bugs. |
| Project `viewer` | 1 project| Read-only. Can export reports.                         |
| API token        | 1 project| Permissions inherited from the issuing user.           |

Per-endpoint details live in [Members & API tokens](members-and-tokens.md). Groups can grant any of the project roles to many users at once — see [Groups](groups.md).
