"""Outbound webhook dispatcher.

Each delivery:

1. Builds the signed envelope (event type + UTC timestamp + payload).
2. POSTs the JSON body to the webhook URL with three exponential retries
   (1s, 10s, 60s) for connection failures and 5xx responses.
3. Persists a single ``WebhookDelivery`` row that holds the final outcome —
   succeeded + status_code on 2xx, otherwise the last error + 4xx body excerpt.

Dispatch runs inside ``BackgroundTasks`` so the originating request returns
without blocking on the remote endpoint.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import BackgroundTasks

from testjam import database
from testjam.models.webhook import Webhook, WebhookDelivery


log = logging.getLogger("testjam.webhooks")

REQUEST_TIMEOUT_SECONDS = 10
RETRY_DELAYS_SECONDS: tuple[int, ...] = (1, 10, 60)
RESPONSE_EXCERPT_LIMIT = 2048
SIGNATURE_HEADER = "X-Testjam-Signature"
EVENT_HEADER = "X-Testjam-Event"
DELIVERY_HEADER = "X-Testjam-Delivery"


def generate_secret() -> str:
    return secrets.token_hex(24)


def build_envelope(event_type: str, payload: dict[str, Any], project_id: int) -> dict[str, Any]:
    return {
        "event": event_type,
        "delivered_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "data": payload,
    }


def sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def schedule_dispatch(
    background: BackgroundTasks | None,
    webhook_id: int,
    event_type: str,
    envelope: dict[str, Any],
) -> None:
    if background is None:
        return
    background.add_task(_run_dispatch, webhook_id, event_type, envelope)


async def _run_dispatch(webhook_id: int, event_type: str, envelope: dict[str, Any]) -> None:
    with database.SessionLocal() as db:
        webhook = db.get(Webhook, webhook_id)
        if webhook is None or not webhook.is_active:
            return
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=envelope,
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        url = webhook.url
        secret = webhook.secret

    body = json.dumps(envelope, sort_keys=True).encode("utf-8")
    signature = sign(secret, body)
    headers = {
        "Content-Type": "application/json",
        SIGNATURE_HEADER: signature,
        EVENT_HEADER: event_type,
        DELIVERY_HEADER: str(delivery.id),
        "User-Agent": "Testjam-Webhook/1",
    }

    succeeded = False
    status_code: int | None = None
    response_excerpt: str | None = None
    last_error: str | None = None
    attempt = 0

    for attempt_index in range(len(RETRY_DELAYS_SECONDS) + 1):
        attempt = attempt_index + 1
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(url, content=body, headers=headers)
            status_code = response.status_code
            response_excerpt = response.text[:RESPONSE_EXCERPT_LIMIT] or None
            if 200 <= response.status_code < 300:
                succeeded = True
                last_error = None
                break
            last_error = f"HTTP {response.status_code}"
            if response.status_code < 500:
                break
        except httpx.HTTPError as exc:
            status_code = None
            response_excerpt = None
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt_index < len(RETRY_DELAYS_SECONDS):
            await asyncio.sleep(RETRY_DELAYS_SECONDS[attempt_index])

    with database.SessionLocal() as db:
        row = db.get(WebhookDelivery, delivery.id)
        if row is None:
            return
        row.attempt_count = attempt
        row.status_code = status_code
        row.response_excerpt = response_excerpt
        row.last_error = last_error
        row.succeeded = succeeded
        row.completed_at = datetime.now(timezone.utc)
        db.commit()

    log.info(
        "webhook.delivery.complete webhook_id=%s event=%s status=%s succeeded=%s attempt=%s",
        webhook_id, event_type, status_code, succeeded, attempt,
    )
