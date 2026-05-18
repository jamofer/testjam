"""Domain logic for project integrations + bug external links.

Routers stay thin: they validate auth + project access, then call into here.
All provider interaction goes through ``services.integrations`` so each
provider stays swappable.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from testjam.models.bug import Bug
from testjam.models.integration import (
    BugExternalLink,
    IntegrationCredential,
    ProjectIntegration,
)
from testjam.models.user import User
from testjam.services import integration_crypto
from testjam.services.integrations import (
    ExternalTicket,
    ProviderConfigError,
    ProviderRequestError,
    get_provider,
)


def ensure_encryption_available() -> None:
    if not integration_crypto.is_available():
        raise HTTPException(
            status_code=503,
            detail="Integration credentials cannot be stored — INTEGRATION_ENCRYPTION_KEY is not configured",
        )


def create_integration(
    db: Session,
    *,
    project_id: int,
    provider_key: str,
    name: str,
    config: dict,
    status_mapping: dict[str, str],
    is_active: bool,
    secret: str,
    actor: User,
) -> ProjectIntegration:
    ensure_encryption_available()
    provider = _provider_or_400(provider_key)
    validated_config = _validate_provider_config(provider, config)
    integration = ProjectIntegration(
        project_id=project_id,
        provider=provider.key,
        name=name,
        config=validated_config,
        status_mapping=status_mapping,
        is_active=is_active,
    )
    integration.credential = IntegrationCredential(
        secret_encrypted=integration_crypto.encrypt(secret),
        created_by_id=actor.id,
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


def update_integration(
    db: Session,
    integration: ProjectIntegration,
    *,
    name: str | None,
    config: dict | None,
    status_mapping: dict[str, str] | None,
    is_active: bool | None,
) -> ProjectIntegration:
    if name is not None:
        integration.name = name
    if config is not None:
        provider = _provider_or_400(integration.provider)
        integration.config = _validate_provider_config(provider, config)
    if status_mapping is not None:
        integration.status_mapping = status_mapping
    if is_active is not None:
        integration.is_active = is_active
    db.commit()
    db.refresh(integration)
    return integration


def rotate_credential(
    db: Session, integration: ProjectIntegration, *, secret: str, actor: User,
) -> ProjectIntegration:
    ensure_encryption_available()
    if integration.credential is None:
        integration.credential = IntegrationCredential(
            secret_encrypted=integration_crypto.encrypt(secret),
            created_by_id=actor.id,
        )
    else:
        integration.credential.secret_encrypted = integration_crypto.encrypt(secret)
        integration.credential.created_by_id = actor.id
        integration.credential.last_used_at = None
    db.commit()
    db.refresh(integration)
    return integration


def health_check(integration: ProjectIntegration) -> None:
    provider = _provider_or_400(integration.provider)
    secret = _decrypt_or_raise(integration)
    try:
        provider.health_check(integration.config, secret)
    except ProviderConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def push_bug_to_integration(
    db: Session,
    bug: Bug,
    integration: ProjectIntegration,
    *,
    labels: list[str] | None,
    actor: User,
) -> BugExternalLink:
    if integration.project_id != bug.project_id:
        raise HTTPException(status_code=400, detail="Integration belongs to a different project")
    if not integration.is_active:
        raise HTTPException(status_code=400, detail="Integration is disabled")
    provider = _provider_or_400(integration.provider)
    secret = _decrypt_or_raise(integration)
    ticket = _create_remote_ticket(provider, integration, secret, bug, labels)
    _stamp_credential_use(integration)
    link = BugExternalLink(
        bug_id=bug.id,
        integration_id=integration.id,
        provider=integration.provider,
        external_id=ticket.external_id,
        url=ticket.url,
        status_raw=ticket.status_raw,
        status_normalized=ticket.status_normalized,
        last_synced_at=datetime.now(timezone.utc),
        created_by_id=actor.id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def sync_bug_link(db: Session, link: BugExternalLink) -> BugExternalLink:
    if link.integration is None:
        raise HTTPException(status_code=400, detail="Link is not tied to an active integration")
    integration = link.integration
    provider = _provider_or_400(integration.provider)
    secret = _decrypt_or_raise(integration)
    try:
        ticket = provider.fetch_status(integration.config, secret, link.external_id)
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _stamp_credential_use(integration)
    link.status_raw = ticket.status_raw
    link.status_normalized = provider.normalize_status(ticket.status_raw, integration.status_mapping)
    link.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(link)
    return link


def delete_link(db: Session, link: BugExternalLink) -> None:
    db.delete(link)
    db.commit()


def _provider_or_400(key: str):
    try:
        return get_provider(key)
    except ProviderConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _validate_provider_config(provider, config: dict) -> dict:
    try:
        return provider.validate_config(config)
    except ProviderConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _decrypt_or_raise(integration: ProjectIntegration) -> str:
    if integration.credential is None:
        raise HTTPException(status_code=400, detail="Integration has no credential")
    ensure_encryption_available()
    try:
        return integration_crypto.decrypt(integration.credential.secret_encrypted)
    except integration_crypto.IntegrationDecryptError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _create_remote_ticket(
    provider, integration: ProjectIntegration, secret: str, bug: Bug, labels: list[str] | None,
) -> ExternalTicket:
    try:
        return provider.create_ticket(
            integration.config,
            secret,
            title=bug.title,
            body_markdown=bug.description or "",
            labels=labels or _default_labels(bug),
        )
    except ProviderConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _default_labels(bug: Bug) -> list[str]:
    out = [f"severity:{bug.severity}"]
    for tag in bug.tags or []:
        out.append(str(tag))
    return out


def _stamp_credential_use(integration: ProjectIntegration) -> None:
    if integration.credential is not None:
        integration.credential.last_used_at = datetime.now(timezone.utc)
