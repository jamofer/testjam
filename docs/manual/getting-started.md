# Getting started

> Traducción: [getting-started.es.md](getting-started.es.md).

This page walks you from a blank machine to a logged-in Testjam UI.

## Prerequisites

- A host with Docker Engine ≥ 24 and the Compose plugin.
- Outbound HTTPS to pull the official images (or a mirror configured on the host).
- (Optional) A reverse proxy with TLS termination — Caddy, nginx, Cloudflare Tunnel, … — pointing at the exposed `APP_PORT`.

The bundled stack ships three long-running containers:

| Container | Image                  | Role                                                            |
|-----------|------------------------|-----------------------------------------------------------------|
| `db`      | `postgres:18.3-alpine` | Persistent database, mounted on a named volume.                 |
| `api`     | `testjam-api`          | FastAPI + Uvicorn, runs Alembic migrations on start.            |
| `web`     | `testjam-frontend`     | Nginx serving the built UI and proxying `/api/` to the backend. |

Only the `web` container exposes a host port (`APP_PORT`, default `8080`).

## 1 · Clone & configure

```bash
git clone https://github.com/Jamofer/testjam.git
cd testjam
cp .env.example .env
```

Edit `.env` and fill in **at least** the following entries:

```dotenv
POSTGRES_PASSWORD=please-change-me
SECRET_KEY=$(openssl rand -hex 32)
APP_PORT=8080
```

`SECRET_KEY` signs JWTs — once issued, rotating it invalidates every active session.

## 2 · Start the stack

```bash
docker compose up -d
```

Alembic runs `upgrade head` automatically on every `api` container start. The `db` container is healthchecked; the `api` waits for it before serving.

Confirm the health endpoint:

```bash
curl -fsS http://localhost:8080/api/v1/health
# {"status":"ok","version":"…","db":"ok"}
```

## 3 · Create the first admin

There is **no public signup endpoint**. The very first user is created via a helper script that talks directly to the database:

```bash
docker compose exec api python scripts/create_admin.py \
  --username admin \
  --email admin@example.com \
  --password 'replace-me'
```

The script is idempotent: rerunning with the same username updates the password.

## 4 · Sign in

Open the UI in a browser:

```
http://localhost:8080/login
```

Type your credentials. Testjam stores the JWT in `localStorage` and injects it on every API call.

<p align="center">
  <img src="../screenshots/hero.png" alt="Logged-in landing" width="70%" />
</p>

## 5 · (Optional) Configure email

Password resets and notifications require an SMTP relay. Set the following in `.env` (full list documented in [Administration](admin.md)):

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=postmaster@example.com
SMTP_PASSWORD=…
SMTP_FROM="Testjam <no-reply@example.com>"
SITE_URL=https://testjam.example.com
```

`SITE_URL` is interpolated into the reset-password link templates; pointing it at the wrong domain breaks the flow silently.

## 6 · Next steps

- Build your first project → [Projects](projects.md).
- Hook your CI → [Robot listener](robot-listener.md).
- Invite teammates → [Members & API tokens](members-and-tokens.md).
