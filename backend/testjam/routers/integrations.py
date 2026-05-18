from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi import status as http_status
from sqlalchemy.exc import IntegrityError

from testjam.auth.dependencies import AuthContext, get_auth_context, get_current_user, require_project_access
from testjam.database import get_db
from testjam.models.bug import Bug
from testjam.models.execution import TestExecution, TestResult
from testjam.models.integration import (
    BugExternalLink,
    ProjectIntegration,
)
from testjam.models.user import User
from testjam.schemas.integration import (
    BugExternalLinkCreate,
    BugExternalLinkOut,
    IntegrationCredentialRotate,
    IntegrationProviderDescriptor,
    ProjectIntegrationCreate,
    ProjectIntegrationOut,
    ProjectIntegrationUpdate,
    ResultReportRequest,
    ResultReportResponse,
)
from testjam.services import bug_activity, integration_service
from testjam.services.bug_numbering import next_bug_number
from testjam.services.integrations import list_providers
from testjam.services.permissions import effective_role


OWNER_ROLES = {"owner"}
WRITER_ROLES = {"owner", "tester"}
READER_ROLES = {"owner", "tester", "viewer"}


providers_router = APIRouter(prefix="/integrations", tags=["Integrations"])
projects_router = APIRouter(prefix="/projects", tags=["Integrations"])
integrations_router = APIRouter(prefix="/integrations", tags=["Integrations"])
bugs_router = APIRouter(prefix="/bugs", tags=["Integrations"])
results_router = APIRouter(prefix="/results", tags=["Integrations"])


@providers_router.get("/providers", response_model=list[IntegrationProviderDescriptor])
def list_integration_providers(_: User = Depends(get_current_user)):
    return [
        IntegrationProviderDescriptor(key=provider.key, label=provider.label)
        for provider in list_providers()
    ]


@projects_router.get("/{id}/integrations", response_model=list[ProjectIntegrationOut])
def list_project_integrations(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    _require_role(db, id, current, READER_ROLES)
    rows = (
        db.query(ProjectIntegration)
        .filter(ProjectIntegration.project_id == id)
        .order_by(ProjectIntegration.created_at.asc())
        .all()
    )
    return [_to_out(row) for row in rows]


@projects_router.post(
    "/{id}/integrations",
    response_model=ProjectIntegrationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_project_integration(
    id: int,
    body: ProjectIntegrationCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    _require_role(db, id, current, OWNER_ROLES)
    integration = integration_service.create_integration(
        db,
        project_id=id,
        provider_key=body.provider,
        name=body.name,
        config=body.config,
        status_mapping=body.status_mapping,
        is_active=body.is_active,
        secret=body.secret,
        actor=current,
    )
    return _to_out(integration)


@integrations_router.get("/{id}", response_model=ProjectIntegrationOut)
def get_integration(
    id: int, db: Session = Depends(get_db), ctx: AuthContext = Depends(get_auth_context),
):
    integration = _integration_or_404(db, id)
    _assert_token_scope(ctx, integration.project_id)
    _require_role(db, integration.project_id, ctx.user, READER_ROLES)
    return _to_out(integration)


@integrations_router.put("/{id}", response_model=ProjectIntegrationOut)
def update_integration_endpoint(
    id: int,
    body: ProjectIntegrationUpdate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    integration = _integration_or_404(db, id)
    _assert_token_scope(ctx, integration.project_id)
    _require_role(db, integration.project_id, ctx.user, OWNER_ROLES)
    integration_service.update_integration(
        db,
        integration,
        name=body.name,
        config=body.config,
        status_mapping=body.status_mapping,
        is_active=body.is_active,
    )
    return _to_out(integration)


@integrations_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration_endpoint(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    integration = _integration_or_404(db, id)
    _assert_token_scope(ctx, integration.project_id)
    _require_role(db, integration.project_id, ctx.user, OWNER_ROLES)
    db.delete(integration)
    db.commit()


@integrations_router.post("/{id}/test", status_code=status.HTTP_204_NO_CONTENT)
def test_integration(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    integration = _integration_or_404(db, id)
    _assert_token_scope(ctx, integration.project_id)
    _require_role(db, integration.project_id, ctx.user, WRITER_ROLES)
    integration_service.health_check(integration)


@integrations_router.post("/{id}/rotate-credential", response_model=ProjectIntegrationOut)
def rotate_integration_credential(
    id: int,
    body: IntegrationCredentialRotate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    integration = _integration_or_404(db, id)
    _assert_token_scope(ctx, integration.project_id)
    _require_role(db, integration.project_id, ctx.user, OWNER_ROLES)
    integration_service.rotate_credential(db, integration, secret=body.secret, actor=ctx.user)
    return _to_out(integration)


@bugs_router.get("/{id}/external-links", response_model=list[BugExternalLinkOut])
def list_bug_external_links(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _bug_or_404(db, id)
    _assert_token_scope(ctx, bug.project_id)
    _require_role(db, bug.project_id, ctx.user, READER_ROLES)
    rows = (
        db.query(BugExternalLink)
        .filter(BugExternalLink.bug_id == bug.id)
        .order_by(BugExternalLink.created_at.asc())
        .all()
    )
    return rows


@bugs_router.post(
    "/{id}/external-links",
    response_model=BugExternalLinkOut,
    status_code=status.HTTP_201_CREATED,
)
def push_bug_external_link(
    id: int,
    body: BugExternalLinkCreate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _bug_or_404(db, id)
    _assert_token_scope(ctx, bug.project_id)
    _require_role(db, bug.project_id, ctx.user, WRITER_ROLES)
    integration = _integration_or_404(db, body.integration_id)
    return integration_service.push_bug_to_integration(
        db, bug, integration, labels=body.labels, actor=ctx.user,
    )


@bugs_router.post("/{id}/external-links/{link_id}/sync", response_model=BugExternalLinkOut)
def sync_bug_external_link(
    id: int,
    link_id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _bug_or_404(db, id)
    _assert_token_scope(ctx, bug.project_id)
    _require_role(db, bug.project_id, ctx.user, WRITER_ROLES)
    link = _link_or_404(db, bug.id, link_id)
    return integration_service.sync_bug_link(db, link)


@bugs_router.delete("/{id}/external-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug_external_link(
    id: int,
    link_id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _bug_or_404(db, id)
    _assert_token_scope(ctx, bug.project_id)
    _require_role(db, bug.project_id, ctx.user, WRITER_ROLES)
    link = _link_or_404(db, bug.id, link_id)
    integration_service.delete_link(db, link)


def _to_out(integration: ProjectIntegration) -> ProjectIntegrationOut:
    credential = integration.credential
    return ProjectIntegrationOut(
        id=integration.id,
        project_id=integration.project_id,
        provider=integration.provider,
        name=integration.name,
        config=integration.config,
        status_mapping=integration.status_mapping,
        is_active=integration.is_active,
        has_credential=credential is not None,
        credential_expires_at=credential.expires_at if credential else None,
        credential_last_used_at=credential.last_used_at if credential else None,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


def _integration_or_404(db: Session, integration_id: int) -> ProjectIntegration:
    integration = db.get(ProjectIntegration, integration_id)
    if integration is None:
        raise HTTPException(status_code=404, detail="Not found")
    return integration


def _bug_or_404(db: Session, bug_id: int) -> Bug:
    bug = db.get(Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Not found")
    return bug


def _link_or_404(db: Session, bug_id: int, link_id: int) -> BugExternalLink:
    link = (
        db.query(BugExternalLink)
        .filter(BugExternalLink.id == link_id, BugExternalLink.bug_id == bug_id)
        .first()
    )
    if link is None:
        raise HTTPException(status_code=404, detail="Not found")
    return link


def _require_role(db: Session, project_id: int, user: User, allowed: set[str]) -> None:
    if user.is_admin:
        return
    role = effective_role(db, user.id, project_id)
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient project role")


@results_router.post(
    "/{id}/report-external",
    response_model=ResultReportResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def report_bug_from_result(
    id: int,
    body: ResultReportRequest,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    result = db.get(TestResult, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    execution = db.get(TestExecution, result.execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    project_id = execution.project_id
    _assert_token_scope(ctx, project_id)
    _require_role(db, project_id, ctx.user, WRITER_ROLES)

    integration: ProjectIntegration | None = None
    if body.integration_id is not None:
        integration = _integration_or_404(db, body.integration_id)
        if integration.project_id != project_id:
            raise HTTPException(
                status_code=400, detail="Integration belongs to a different project",
            )

    bug = _create_bug_from_result(db, project_id, execution, result, body, ctx.user)
    link: BugExternalLink | None = None
    if integration is not None:
        link = integration_service.push_bug_to_integration(
            db, bug, integration, labels=body.labels or None, actor=ctx.user,
        )
    return ResultReportResponse(
        bug_id=bug.id,
        bug_number=bug.number,
        external_link=BugExternalLinkOut.model_validate(link) if link else None,
    )


def _create_bug_from_result(
    db: Session,
    project_id: int,
    execution: TestExecution,
    result: TestResult,
    body: ResultReportRequest,
    actor: User,
) -> Bug:
    for attempt in range(5):
        bug = Bug(
            project_id=project_id,
            number=next_bug_number(db, project_id),
            title=body.title,
            description=body.description,
            severity=body.severity,
            status="open",
            tags=body.tags or None,
            result_id=result.id,
            execution_id=execution.id,
            version_id=execution.version_id,
            environment=execution.environment,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        try:
            db.add(bug)
            db.flush()
            break
        except IntegrityError:
            db.rollback()
    else:
        raise HTTPException(status_code=409, detail="Could not allocate bug number")
    bug_activity.record_status_change(db, bug.id, None, "open", actor.id)
    db.commit()
    db.refresh(bug)
    return bug


def _assert_token_scope(ctx: AuthContext, project_id: int) -> None:
    if ctx.project_scope is not None and ctx.project_scope != project_id:
        raise HTTPException(
            status_code=403,
            detail="API token is not authorized for this project",
        )
