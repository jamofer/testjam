from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


WebhookEvent = Literal[
    "execution.created",
    "execution.completed",
    "execution.aborted",
    "test_result.failed",
    "bug.created",
    "bug.resolved",
    "bug.status_changed",
]

ALL_WEBHOOK_EVENTS: tuple[str, ...] = tuple(WebhookEvent.__args__)  # type: ignore[attr-defined]


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: HttpUrl
    events: list[WebhookEvent] = Field(min_length=1)
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    url: HttpUrl | None = None
    events: list[WebhookEvent] | None = None
    is_active: bool | None = None


class WebhookOut(BaseModel):
    id: int
    project_id: int
    name: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookWithSecret(WebhookOut):
    secret: str


class WebhookDeliveryOut(BaseModel):
    id: int
    webhook_id: int
    event_type: str
    status_code: int | None
    attempt_count: int
    succeeded: bool
    last_error: str | None
    response_excerpt: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
