#!/bin/sh
# Volumes created by earlier releases belong to root, so ownership is fixed
# before dropping privileges.
set -eu

APP_USER=testjam
UPLOAD_DIR="${UPLOAD_DIR:-/app/uploads}"

if [ "$(id -u)" = "0" ]; then
    chown -R "$APP_USER:$APP_USER" "$UPLOAD_DIR"
    exec setpriv --reuid="$APP_USER" --regid="$APP_USER" --init-groups "$0" "$@"
fi

: "${SECRET_KEY:?SECRET_KEY env var is required (generate with: openssl rand -hex 32)}"
: "${DATABASE_URL:?DATABASE_URL env var is required}"

alembic upgrade head
exec "$@"
