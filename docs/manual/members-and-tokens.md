# Members & API tokens

> Traducción: [members-and-tokens.es.md](members-and-tokens.es.md).

Testjam authentication has two layers:

- **Users** — humans with a username, password and a global flag `is_admin`.
- **Project members** — a user added to a specific project with a role (`owner` / `editor` / `viewer`).

API access for machines piggy-backs on either:

- The user's **JWT** (issued at `/auth/login`).
- A **scoped API token** issued from a project's members page.

## Members page

Navigate to **Project → Members** (`/projects/:id/members`). Two panels:

### Members panel

| Column   | Description                                                                |
|----------|----------------------------------------------------------------------------|
| User     | Display name + username + admin / deleted badges.                          |
| Email    | Used by notifications and password resets.                                  |
| Role     | `owner` · `editor` · `viewer`. Dropdown to change (owner/admin only).      |
| Last seen| Timestamp of last successful login.                                         |
| Actions  | Remove from project. Owner role removal forces a successor.                |

Adding a member opens a dialog with autocomplete against the user directory. If the email is not in the directory, the form falls back to a "send invitation" path (currently only visible to admins).

### Project API tokens panel

| Column   | Description                                                          |
|----------|----------------------------------------------------------------------|
| Name     | Free-form identifier ("CI staging", "Robot listener").              |
| Created  | Issuance timestamp + creator.                                        |
| Last used| Timestamp of last successful authenticated request.                  |
| Expires  | Optional. After this date the token returns 401.                     |
| Actions  | Copy (only on issuance), regenerate, revoke.                         |

Token format: `tjm_<32 random base32 chars>`. Tokens are shown **once** at issuance — losing the value forces a regenerate.

Every request authenticated with `X-API-Key` returns 403 if it touches a project different from the token's `project_scope`. Listing endpoints (`GET /projects`, `GET /users`) require a JWT.

## Roles in detail

| Action                                | viewer | editor | owner | global admin |
|---------------------------------------|:------:|:------:|:-----:|:------------:|
| Read suites / cases / plans / runs    | ✓      | ✓      | ✓     | ✓            |
| Export reports                        | ✓      | ✓      | ✓     | ✓            |
| Create / edit suites and cases        |        | ✓      | ✓     | ✓            |
| Create / edit plans and executions    |        | ✓      | ✓     | ✓            |
| Manage project members                |        |        | ✓     | ✓            |
| Issue / revoke API tokens             |        |        | ✓     | ✓            |
| Archive / unarchive project           |        |        | ✓     | ✓            |
| Delete project (planned)              |        |        |       | ✓            |
| Instance settings, users, backups     |        |        |       | ✓            |

## Authenticating to the API

### Bearer (user) token

```bash
TOKEN=$(curl -s -X POST $API/auth/login \
  -d 'username=alice&password=hunter2' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" $API/projects
```

### Project API key

```bash
curl -H "X-API-Key: tjm_abcdefghij…" $API/projects/$PID/cases
```

Both headers may be sent on the same request — the API key takes precedence if both are present and valid.

## API quick reference

| Endpoint                                       | Verb   | Purpose                                |
|------------------------------------------------|--------|----------------------------------------|
| `/api/v1/auth/login`                           | POST   | Issue a JWT.                           |
| `/api/v1/auth/refresh`                         | POST   | Rotate the JWT.                        |
| `/api/v1/users/me`                             | GET    | Current user profile.                  |
| `/api/v1/projects/{id}/members`                | GET    | List project members.                  |
| `/api/v1/projects/{id}/members`                | POST   | Add a member.                          |
| `/api/v1/projects/{id}/members/{user_id}`      | PATCH  | Change role.                           |
| `/api/v1/projects/{id}/members/{user_id}`      | DELETE | Remove member.                         |
| `/api/v1/projects/{id}/api-tokens`             | GET    | List project API tokens.               |
| `/api/v1/projects/{id}/api-tokens`             | POST   | Issue a new API token.                 |
| `/api/v1/projects/{id}/api-tokens/{token_id}`  | DELETE | Revoke an API token.                   |
