# Planned features

> Traducción: [README.es.md](README.es.md).

This folder describes features that are **planned** but **not yet available** in Testjam v1.0. Each page captures the user-facing goal, the data model sketch, the API endpoints we expect to ship, and the open design questions.

These pages are **forward-looking**. Anything here may change without notice until the feature ships and is merged into the [user manual](../manual/README.md).

## Index

| Feature | Status | Driver |
|---------|--------|--------|
| [Docker runner](docker-runner.md) | Not started | Run automatic tests without an external CI worker. |
| [Multi-tenant orgs](multi-tenant.md) | Not started | Organizations as a layer above projects (only if Testjam moves to managed hosting). |

## Conventions on these pages

Every planned page follows the same skeleton:

1. **Why** — the user-facing problem.
2. **What you will see** — a sketch of the UI / UX.
3. **Data model** — new tables, columns, relationships.
4. **API** — endpoint table.
5. **Open questions** — design decisions still being made.
6. **Out of scope** — explicit exclusions to bound the work.

A page is moved from `planned/` to `manual/` once the feature is fully merged.

## Shipped in v1.0 (formerly planned)

Bug tracking, project dashboards, dark mode, outgoing webhooks, external linking to Jira / GitHub / GitLab / Azure DevOps / OpenProject, groups with role inheritance, and extended admin operations all shipped with v1.0 and now live in the user manual.
