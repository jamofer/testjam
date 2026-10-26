"""Webhook management endpoints.

Two routers, both gated by project-owner permissions:

- ``/projects/{id}/webhooks`` — list + create + delivery log filter.
- ``/webhooks/{id}`` — read / update / delete a specific webhook, fire a
  manual test ping, list its recent deliveries.

The secret returned on create is the only opportunity to copy it: subsequent
reads omit it. Owners who lose the secret can rotate by updating the webhook
(server regenerates).
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from testjam.auth.dependencies import AuthContext, authorize_project, get_auth_context
from testjam.database import get_db
from testjam.models.webhook import Webhook, WebhookDelivery
from testjam.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryOut,
    WebhookOut,
    WebhookUpdate,
    WebhookWithSecret,
)
from testjam.services import webhook_dispatch
from testjam.services.permissions import OWNER_ROLES


projects_router = APIRouter(prefix="/projects", tags=["Webhooks"])
webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

DELIVERY_LIST_LIMIT_MAX = 100
DELIVERY_LIST_LIMIT_DEFAULT = 25


def _get_webhook(db: Session, webhook_id: int) -> Webhook:
    webhook = db.get(Webhook, webhook_id)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Not found")
    return webhook


@projects_router.get("/{id}/webhooks", response_model=list[WebhookOut])
def list_webhooks(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    authorize_project(db, ctx, id, OWNER_ROLES)
    return (
        db.query(Webhook)
        .filter(Webhook.project_id == id)
        .order_by(Webhook.created_at.desc())
        .all()
    )


@projects_router.post(
    "/{id}/webhooks", response_model=WebhookWithSecret, status_code=status.HTTP_201_CREATED,
)
def create_webhook(
    id: int,
    body: WebhookCreate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    authorize_project(db, ctx, id, OWNER_ROLES)
    webhook = Webhook(
        project_id=id,
        name=body.name,
        url=str(body.url),
        secret=webhook_dispatch.generate_secret(),
        events=list(body.events),
        is_active=body.is_active,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return WebhookWithSecret.model_validate(webhook)


@webhooks_router.get("/{id}", response_model=WebhookOut)
def get_webhook(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    webhook = _get_webhook(db, id)
    authorize_project(db, ctx, webhook.project_id, OWNER_ROLES)
    return webhook


@webhooks_router.put("/{id}", response_model=WebhookOut)
def update_webhook(
    id: int,
    body: WebhookUpdate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    webhook = _get_webhook(db, id)
    authorize_project(db, ctx, webhook.project_id, OWNER_ROLES)
    data = body.model_dump(exclude_unset=True)
    if "url" in data and data["url"] is not None:
        data["url"] = str(data["url"])
    if "events" in data and data["events"] is not None:
        data["events"] = list(data["events"])
    for field, value in data.items():
        setattr(webhook, field, value)
    db.commit()
    db.refresh(webhook)
    return webhook


@webhooks_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    webhook = _get_webhook(db, id)
    authorize_project(db, ctx, webhook.project_id, OWNER_ROLES)
    db.delete(webhook)
    db.commit()


@webhooks_router.post("/{id}/test", response_model=WebhookOut)
def test_webhook(
    id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    webhook = _get_webhook(db, id)
    authorize_project(db, ctx, webhook.project_id, OWNER_ROLES)
    envelope = webhook_dispatch.build_envelope(
        "webhook.test",
        {"message": "ping from Testjam", "webhook_id": webhook.id},
        webhook.project_id,
    )
    webhook_dispatch.schedule_dispatch(background, webhook.id, "webhook.test", envelope)
    return webhook


@webhooks_router.get("/{id}/deliveries", response_model=list[WebhookDeliveryOut])
def list_deliveries(
    id: int,
    limit: int = DELIVERY_LIST_LIMIT_DEFAULT,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    webhook = _get_webhook(db, id)
    authorize_project(db, ctx, webhook.project_id, OWNER_ROLES)
    capped = max(1, min(limit, DELIVERY_LIST_LIMIT_MAX))
    return (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.webhook_id == webhook.id)
        .order_by(WebhookDelivery.created_at.desc(), WebhookDelivery.id.desc())
        .limit(capped)
        .all()
    )
