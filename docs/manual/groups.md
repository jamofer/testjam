# Groups

> Traducción: [groups.es.md](groups.es.md).

Groups bundle users so admins can grant project access by group instead of one user at a time. When a group is assigned to a project with a role, every member of that group inherits that role on that project — without an explicit per-user `ProjectMember` row.

## Why groups

Without groups, onboarding a 12-person QA team to ten projects is 120 manual `add member` operations. With groups: create a `QA Team` group once, assign each project to it once, total 22 operations. Removing the person from the group revokes their access on all ten projects instantly.

## Managing groups

Group definitions are global, managed by admins under **Users (admin) → Groups**:

- **New group** — name + optional description
- **Add / remove members** — pick from the user list
- **Rename / delete** — delete only allowed if no project assignments reference the group

A user can belong to multiple groups simultaneously.

## Assigning a group to a project

**Project → Members → Group access** lists every group assigned to the current project. The **Assign group** form picks a candidate group and a role (`owner` / `tester` / `viewer`). The group's members instantly gain that role on the project.

If no candidate groups appear, the section explains why:

- *No groups exist yet.* — go to the Users admin and create one first
- *Every existing group is already assigned to this project.* — re-assign with a different role or unassign first

## Role resolution

A user can have **direct** project membership (their own `ProjectMember` row) plus **indirect** membership via one or more groups. The effective role is the highest-privileged one across all sources:

```
owner > tester > viewer
```

So a user who is a `viewer` directly but a member of a group assigned as `tester` gets `tester` on that project. Admins always have implicit `owner` on every project.

## Editing the role of a group on a project

Use the role select next to the group in the project Members page. The change applies to every member of the group on this project — confirm with care.

## Removing a group from a project

The trash icon next to the group revokes the role for every member of that group on this project. Members still in the group keep their access to other projects where the group is assigned.

## Auditing

Group assignments are listed in the project Members page alongside direct members. Both are visible to any project member (viewer included) — useful for understanding why someone has access.

There's no per-group activity log in v1.0; group changes are logged at the admin level only.

## Permissions

| Action | Required role |
|--------|---------------|
| List groups (global) | any authenticated user (admins see all, others see groups they belong to) |
| Create / edit / delete group | admin |
| Assign group to project, change role, unassign | owner / admin |

## Limits and gotchas

- A user removed from a group loses their inherited project access on the next request. Currently open sessions don't get force-logged-out — they hit a 403 on the next mutation and the UI handles it gracefully.
- Group access is additive only; there's no "deny" rule. To revoke, drop the user from the group or unassign the group from the project.
- Deleting a group fails with `409 Conflict` if any project still references it. Unassign first.
