# Outgoing webhooks

> Traducción: [webhooks.es.md](webhooks.es.md).

Webhooks let external systems react to events in Testjam in near real time: trigger a build, post to a chat channel, sync to a data warehouse, page on-call, anything HTTP. Every delivery is signed with HMAC so the receiver can verify authenticity and replay-protect.

## Configuration

**Project → Webhooks** lists every webhook configured for the project plus its recent delivery log. **New webhook** opens a dialog with:

- **URL** — full HTTPS endpoint (the receiver)
- **Secret** — opaque string used to sign every payload; rotate any time
- **Events** — multi-select of the event types to subscribe to (see table below)
- **Description** — free text, optional

A webhook can be paused (toggle) without losing its delivery history. Pausing stops new deliveries; the active deliveries finish their retry budget.

## Event catalog

| Event | Fires when |
|-------|------------|
| `execution.created` | A new execution is created |
| `execution.completed` | An execution transitions to `completed` |
| `execution.aborted` | An execution transitions to `aborted` |
| `result.updated` | A result's status changes (pass / fail / blocked / not_run) |
| `bug.created` | A new bug is reported |
| `bug.status_changed` | A bug transitions between statuses |
| `bug.commented` | A comment is added to a bug |

Add more events on request — the framework is generic.

## Payload format

Every payload is JSON with a stable envelope:

```json
{
  "event": "bug.created",
  "delivered_at": "2026-05-25T12:34:56.789Z",
  "project_id": 42,
  "data": { "id": 123, "number": 7, "title": "Login broken", "severity": "high", "status": "open", "..." }
}
```

`data` is the serialized resource as returned by `GET /<resource>/<id>`. Fields are stable across patch releases.

## HMAC signing

Each request carries a `X-Testjam-Signature` header:

```
X-Testjam-Signature: sha256=<hex digest>
```

The digest is `HMAC-SHA256(secret, raw_request_body)`. The receiver should:

1. Read the raw body before parsing JSON.
2. Compute `HMAC-SHA256(your_stored_secret, raw_body)`.
3. Compare using a constant-time comparison.
4. Reject the request on mismatch (return non-2xx; Testjam will retry).

Additional headers:

- `X-Testjam-Event` — the event type
- `X-Testjam-Delivery-Id` — opaque id for idempotency
- `X-Testjam-Timestamp` — ISO-8601 UTC, also inside the body

## Delivery, retries, and the log

A delivery is attempted with a 10 s timeout. If the receiver returns 5xx, times out, or fails DNS, Testjam retries with exponential backoff (1 min, 5 min, 15 min, 1 h, 6 h). After ~24 h of failures the delivery is marked permanently failed.

The delivery log per webhook shows status code, latency, attempt count, and the response body (truncated). A failed delivery can be redelivered manually from the log.

## Permissions

Webhook configuration requires **owner** or **admin**. Tester / viewer cannot list or modify webhooks. Project-scoped API tokens can be used by external callers; webhook payloads include no authentication material themselves.

## Security recommendations

- Always use HTTPS endpoints. Testjam refuses `http://` URLs unless `ALLOW_INSECURE_WEBHOOKS=1` is set explicitly.
- Rotate the secret periodically. Old secrets become invalid the moment you save the new one.
- Verify the signature on every request. Do not trust event type or payload before validating.
- Use the `X-Testjam-Delivery-Id` header for idempotency; Testjam may redeliver after a recoverable failure.
