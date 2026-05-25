# Plans

> Traducción: [plans.es.md](plans.es.md).

A **test plan** is a curated, versioned set of cases. Plans are how you say *"these are the cases I want exercised for v1.4.0"*. A case can belong to many plans (M2M), and a plan can pull cases from any suite of the project.

## Mental model

```
Project ── Plan ── (M2M) ── Case ── Step
                 \
                  └── pinned to → Version
```

Plans never own cases — they reference them. Editing a case from inside a plan edits the underlying library; you cannot "fork" a case into a plan.

## Create

Navigate to **Project → Plans** and click **New plan**.

| Field         | Required | Notes                                                          |
|---------------|----------|----------------------------------------------------------------|
| `name`        | yes      | E.g. *Smoke v1.4* or *Release candidate 2026-Q2*.              |
| `description` | no       | Markdown. Renders on the plan detail page.                     |
| `version_id`  | no       | Pin the plan to one of the project [versions](#versions). Used as the default in the New Execution dialog. |

## Adding cases

From the plan detail page (`/plans/:id`):

- **+ Add cases** opens a picker rooted at the project suite tree. Select individual cases or whole suites — the picker recurses.
- The selected cases appear in the plan's ordered list. Reorder with drag-and-drop.
- Remove with the trash icon on each row — this only removes the link, the case stays in the library.

## Versions

Versions are simple labels managed at **Project → Versions** (`/projects/:id/versions`). They are linked from plans and from executions, and they appear in the version column of the exports.

Typical usage:

- Create one version per software release (`1.0.0`, `1.1.0`, …).
- Pin each plan to the version it was authored for.
- When executing the plan, override the version only when re-running historical plans.

## Running a plan

Click **Run plan** on the plan detail page. The button opens the **New execution** dialog with the plan and version pre-filled. Continue at [Executions](executions.md).

## API quick reference

| Endpoint                                  | Verb   | Purpose                                |
|-------------------------------------------|--------|----------------------------------------|
| `/api/v1/projects/{id}/plans`             | GET    | List plans in a project.               |
| `/api/v1/projects/{id}/plans`             | POST   | Create plan.                           |
| `/api/v1/plans/{id}`                      | GET    | Read plan with its cases.              |
| `/api/v1/plans/{id}`                      | PATCH  | Update name / description / version.   |
| `/api/v1/plans/{id}/cases`                | POST   | Attach cases (body: `{case_ids:[…]}`). |
| `/api/v1/plans/{id}/cases/{case_id}`      | DELETE | Detach a case from the plan.           |
| `/api/v1/plans/{id}/cases/reorder`        | POST   | Rewrite case order inside the plan.    |
| `/api/v1/projects/{id}/versions`          | GET    | List versions.                         |
| `/api/v1/projects/{id}/versions`          | POST   | Create version.                        |
