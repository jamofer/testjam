#!/usr/bin/env bash
# Periodic backup of the Testjam Postgres database and uploads volume.
#
# Designed to run on the host alongside docker compose. The `db` service must
# be named `db` and the `api` service must mount uploads at /app/uploads.
#
# Environment:
#   BACKUP_DIR        Where to write archives. Default: ./backups
#   RETENTION_DAYS    Delete archives older than this. Default: 14
#   COMPOSE_PROJECT   Docker compose project name. Optional; auto-detected.
#   POSTGRES_USER     Used for pg_dump auth. Default: testjam
#   POSTGRES_DB       Database name. Default: testjam
#
# Usage:
#   scripts/backup.sh
#   BACKUP_DIR=/var/backups/testjam RETENTION_DAYS=30 scripts/backup.sh
#
# Output:
#   $BACKUP_DIR/testjam-YYYYMMDD-HHMMSS.tar.gz
#       ├── dump.sql      (pg_dump --clean --if-exists)
#       └── uploads/      (tar of /app/uploads from the api container)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
POSTGRES_USER="${POSTGRES_USER:-testjam}"
POSTGRES_DB="${POSTGRES_DB:-testjam}"

timestamp="$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT

echo "[backup] dumping database $POSTGRES_DB"
docker compose exec -T db pg_dump \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --clean --if-exists --no-owner --no-privileges \
    > "$staging/dump.sql"

echo "[backup] archiving uploads volume"
docker compose exec -T api tar -C /app -cf - uploads > "$staging/uploads.tar"

archive="$BACKUP_DIR/testjam-$timestamp.tar.gz"
tar -czf "$archive" -C "$staging" dump.sql uploads.tar
echo "[backup] wrote $archive ($(du -h "$archive" | cut -f1))"

if [[ "$RETENTION_DAYS" -gt 0 ]]; then
    echo "[backup] pruning archives older than $RETENTION_DAYS days"
    find "$BACKUP_DIR" -maxdepth 1 -type f -name 'testjam-*.tar.gz' \
        -mtime "+$RETENTION_DAYS" -print -delete
fi
