# Multi-tenant orgs — Planned

> Traducción: [multi-tenant.es.md](multi-tenant.es.md). · Status: **Not started · gated**.

## Why

Testjam today is a **single-tenant** system: one instance, one universe of users + projects. Acceptable for self-hosted on a private network, untenable for any SaaS or shared-instance scenario (multiple companies on the same deploy, or one company with multiple isolated business units).

This page is **gated**: we will not start the work until there is real demand for SaaS or for sharing one instance across legally distinct entities.

## What you will see

A new entity layer between `User` and `Project`:

```
Organization ─┬── Project ── …
              └── User (member with org-level role)
```

- A new switcher in the top nav: **<Org name> ▾** with the list of orgs the user belongs to. Switching changes the entire URL scope (`/orgs/:slug/projects/...`).
- A new **Org settings** page (owner / admin of the org only): name, slug, default project visibility, allow-list of email domains for invites.
- A separate billing surface — initially out of scope; lives in the `M.5+` commercial repo.

## Org-level roles

| Org role | Within an org's projects                                            |
|----------|---------------------------------------------------------------------|
| `owner`  | Full power: create / delete projects, manage members, manage billing. |
| `admin`  | Same as owner except billing.                                       |
| `member` | Sees only the projects they were explicitly added to (regular flow).|

A user can belong to many orgs with different roles.

## Data model

```text
Organization
 ├── id, slug, name, created_by, created_at
 ├── settings (json)
 └── members: OrganizationMember[]

OrganizationMember
 ├── id, org_id, user_id, role
 └── added_at

Project gets a new column:
  org_id (NOT NULL)
```

Migration: a default org `"Personal"` is created per existing user; their projects become members of that org. Subsequent merges are manual (admin moves project to a different org).

## API

| Endpoint                                          | Verb   | Purpose                                       |
|---------------------------------------------------|--------|-----------------------------------------------|
| `/api/v1/orgs`                                    | GET    | List orgs the current user belongs to.        |
| `/api/v1/orgs`                                    | POST   | Create a new org.                             |
| `/api/v1/orgs/{slug}`                             | PATCH  | Update org settings.                          |
| `/api/v1/orgs/{slug}/members`                     | GET    | List org members.                             |
| `/api/v1/orgs/{slug}/projects`                    | GET    | List projects of the org.                     |
| `/api/v1/orgs/{slug}/projects`                    | POST   | Create a project in this org.                 |

The existing `/api/v1/projects/...` routes survive but become a thin wrapper that resolves the org from the project ID.

## Open questions

- URL design: `/orgs/<slug>/projects/<slug>` or keep the current flat `/projects/<id>` and only expose orgs in nav? Lean towards flat URLs to minimise churn for self-hosted single-tenant users.
- Cross-org sharing of cases — not initially. Each org is fully siloed.
- Per-org rate limits & quotas — bundled with billing, deferred.

## Out of scope

- Billing / Stripe / license keys — these live in the enterprise repo (`M.8`).
- Tenant isolation at the database level (separate schemas) — not required; row-level scoping by `org_id` is enough for v1.
- SSO at the org level — enterprise (`M.5`).

## Why this is gated

Multi-tenant adds permanent complexity to every endpoint, every test, and every migration. It is worth it only if Testjam moves to SaaS or to shared-instance commercial use. Until that demand is real, the work stays here.
