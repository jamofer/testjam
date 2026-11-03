#!/usr/bin/env bash
# Smoke test for a running production stack (docker-compose.yml).
#
# Goes through the web container like a user would: the SPA, the API docs
# schema and an authenticated attachment upload, which proves the non-root
# api process can write to the uploads volume.
#
# Environment:
#   APP_URL          Base URL of the web container. Default: http://127.0.0.1:8080
#   COMPOSE_FILE     Compose file of the running stack. Default: docker-compose.yml
#
# Usage:
#   scripts/smoke_production_stack.sh
set -euo pipefail

APP_URL="${APP_URL:-http://127.0.0.1:8080}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
SMOKE_USER="smoke"
SMOKE_PASSWORD="smoke-$(date +%s)-password"

fail() {
  echo "smoke test failed: $*" >&2
  exit 1
}

expect_status() {
  local expected="$1" actual="$2" what="$3"
  [[ "$actual" == "$expected" ]] || fail "$what returned HTTP $actual, expected $expected"
}

status=$(curl -s -o /tmp/smoke-index.html -w "%{http_code}" "$APP_URL/")
expect_status 200 "$status" "web root"
grep -qi "<div id=\"root\">" /tmp/smoke-index.html || fail "web root is not the SPA"

status=$(curl -s -o /tmp/smoke-openapi.json -w "%{http_code}" "$APP_URL/api/openapi.json")
expect_status 200 "$status" "openapi schema through the proxy"
jq -e '.paths | length > 0' /tmp/smoke-openapi.json >/dev/null || fail "openapi schema has no paths"

docker compose -f "$COMPOSE_FILE" exec -T api python scripts/create_admin.py \
  --username "$SMOKE_USER" --email smoke@example.com --password "$SMOKE_PASSWORD" >/dev/null

token=$(curl -sf -X POST "$APP_URL/api/v1/auth/login" \
  --data-urlencode "username=$SMOKE_USER" --data-urlencode "password=$SMOKE_PASSWORD" \
  | jq -r .access_token)
[[ -n "$token" && "$token" != "null" ]] || fail "login returned no token"
auth=(-H "Authorization: Bearer $token")

project_id=$(curl -sf "${auth[@]}" -H "Content-Type: application/json" \
  -d '{"name": "Smoke"}' "$APP_URL/api/v1/projects" | jq -r .id)
suite_id=$(curl -sf "${auth[@]}" -H "Content-Type: application/json" \
  -d '{"name": "Smoke suite"}' "$APP_URL/api/v1/projects/$project_id/suites" | jq -r .id)
case_id=$(curl -sf "${auth[@]}" -H "Content-Type: application/json" \
  -d "{\"name\": \"Smoke case\", \"suite_id\": $suite_id}" "$APP_URL/api/v1/suites/$suite_id/cases" | jq -r .id)

echo "smoke evidence" > /tmp/smoke-evidence.txt
status=$(curl -s -o /dev/null -w "%{http_code}" "${auth[@]}" \
  -F "file=@/tmp/smoke-evidence.txt;type=text/plain" "$APP_URL/api/v1/cases/$case_id/attachments")
expect_status 201 "$status" "attachment upload"

echo "production stack smoke test passed"
