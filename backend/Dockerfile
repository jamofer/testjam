# syntax=docker/dockerfile:1.7
FROM python:3.14-slim

# pg_dump must match the server major version or it refuses to run
# (server 18 vs client 17 → "aborting because of server version mismatch").
# Debian's `postgresql-client` defaults to whatever the base image ships;
# pin to PGDG's `postgresql-client-18` so the version stays in lockstep
# with the postgres:18.x image used in docker-compose-dev.yml.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg git \
    && install -d /usr/share/keyrings \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/pgdg.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] http://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-18 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -e ".[dev]"

RUN mkdir -p /app/uploads/cases /app/uploads/results

CMD ["uvicorn", "testjam.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
