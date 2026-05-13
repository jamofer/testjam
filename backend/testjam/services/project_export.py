"""Per-project export: cases + suites + executions + attachments as a single ZIP.

Layout:
    manifest.json              project name, exported_at, app_version
    project.json               nested project data (suites/cases/executions/results)
    attachments/cases/<id>/    case attachment files
    attachments/results/<id>/  result attachment files
    attachments/executions/<id>/  execution-level attachment files
"""

from __future__ import annotations

import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

from sqlalchemy.orm import Session

from testjam.models.execution import (
    ExecutionAttachment,
    ResultAttachment,
    TestExecution,
    TestResult,
    TestStepResult,
)
from testjam.models.project import Project
from testjam.models.testcase import Attachment, SuiteStep, TestCase, TestStep, TestSuite


@dataclass
class ExportArtifact:
    path: str
    filename: str


def export_project(db: Session, project: Project) -> ExportArtifact:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = _safe_slug(project.name)

    fd, archive_path = tempfile.mkstemp(prefix=f"testjam-project-{safe_name}-{timestamp}-", suffix=".zip")
    os.close(fd)

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(_manifest(project), indent=2))
        document, attachment_files = _build_document(db, project)
        zf.writestr("project.json", json.dumps(document, indent=2, default=str))
        for archive_name, source_path in attachment_files:
            if os.path.isfile(source_path):
                zf.write(source_path, archive_name)

    return ExportArtifact(path=archive_path, filename=f"project-{safe_name}-{timestamp}.zip")


def _manifest(project: Project) -> dict:
    return {
        "format_version": 1,
        "app_version": _app_version(),
        "project_id": project.id,
        "project_name": project.name,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_document(db: Session, project: Project) -> tuple[dict, list[tuple[str, str]]]:
    files: list[tuple[str, str]] = []

    suites = db.query(TestSuite).filter(TestSuite.project_id == project.id).order_by(TestSuite.id).all()
    suite_ids = [s.id for s in suites]

    cases = (
        db.query(TestCase)
        .filter(TestCase.suite_id.in_(suite_ids))
        .order_by(TestCase.id)
        .all() if suite_ids else []
    )
    case_ids = [c.id for c in cases]

    steps_by_case = _group_by(
        db.query(TestStep).filter(TestStep.test_case_id.in_(case_ids)).all() if case_ids else [],
        lambda s: s.test_case_id,
    )
    suite_steps_by_suite = _group_by(
        db.query(SuiteStep).filter(SuiteStep.suite_id.in_(suite_ids)).all() if suite_ids else [],
        lambda s: s.suite_id,
    )
    case_attachments_by_case = _group_by(
        db.query(Attachment).filter(Attachment.test_case_id.in_(case_ids)).all() if case_ids else [],
        lambda a: a.test_case_id,
    )

    executions = (
        db.query(TestExecution)
        .filter(TestExecution.project_id == project.id)
        .order_by(TestExecution.id)
        .all()
    )
    execution_ids = [e.id for e in executions]

    results = (
        db.query(TestResult).filter(TestResult.execution_id.in_(execution_ids)).all()
        if execution_ids else []
    )
    result_ids = [r.id for r in results]
    results_by_execution = _group_by(results, lambda r: r.execution_id)

    step_results_by_result = _group_by(
        db.query(TestStepResult).filter(TestStepResult.test_result_id.in_(result_ids)).all()
        if result_ids else [],
        lambda sr: sr.test_result_id,
    )
    result_attachments_by_result = _group_by(
        db.query(ResultAttachment).filter(ResultAttachment.result_id.in_(result_ids)).all()
        if result_ids else [],
        lambda a: a.result_id,
    )
    execution_attachments_by_execution = _group_by(
        db.query(ExecutionAttachment).filter(ExecutionAttachment.execution_id.in_(execution_ids)).all()
        if execution_ids else [],
        lambda a: a.execution_id,
    )

    document = {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at,
            "archived_at": project.archived_at,
        },
        "suites": [_suite_dict(s, suite_steps_by_suite.get(s.id, [])) for s in suites],
        "cases": [
            _case_dict(
                c,
                steps_by_case.get(c.id, []),
                _attachment_dicts(case_attachments_by_case.get(c.id, []), files, f"attachments/cases/{c.id}"),
            )
            for c in cases
        ],
        "executions": [
            _execution_dict(
                ex,
                results_by_execution.get(ex.id, []),
                step_results_by_result,
                result_attachments_by_result,
                files,
                _attachment_dicts(
                    execution_attachments_by_execution.get(ex.id, []),
                    files,
                    f"attachments/executions/{ex.id}",
                ),
            )
            for ex in executions
        ],
    }
    return document, files


def _suite_dict(s: TestSuite, suite_steps: list[SuiteStep]) -> dict:
    return {
        "id": s.id,
        "parent_suite_id": s.parent_suite_id,
        "name": s.name,
        "description": s.description,
        "tags": s.tags,
        "order": s.order,
        "steps": [
            {"id": ss.id, "order": ss.order, "step_type": ss.step_type, "action": ss.action}
            for ss in sorted(suite_steps, key=lambda x: x.order)
        ],
    }


def _case_dict(c: TestCase, steps: list[TestStep], attachments: list[dict]) -> dict:
    return {
        "id": c.id,
        "suite_id": c.suite_id,
        "name": c.name,
        "description": c.description,
        "preconditions": c.preconditions,
        "tags": c.tags,
        "external_id": c.external_id,
        "order": c.order,
        "steps": [
            {
                "id": s.id,
                "order": s.order,
                "step_type": s.step_type,
                "action": s.action,
                "expected_result": s.expected_result,
            }
            for s in sorted(steps, key=lambda x: x.order)
        ],
        "attachments": attachments,
    }


def _execution_dict(
    ex: TestExecution,
    results: list[TestResult],
    step_results_by_result: dict,
    result_attachments_by_result: dict,
    files: list[tuple[str, str]],
    execution_attachments: list[dict],
) -> dict:
    return {
        "id": ex.id,
        "title": ex.title,
        "description": ex.description,
        "type": ex.type,
        "status": ex.status,
        "version": ex.version,
        "environment": ex.environment,
        "started_at": ex.started_at,
        "finished_at": ex.finished_at,
        "created_at": ex.created_at,
        "attachments": execution_attachments,
        "results": [
            {
                "id": r.id,
                "test_case_id": r.test_case_id,
                "status": r.status,
                "comment": r.comment,
                "executed_by": r.executed_by,
                "executed_at": r.executed_at,
                "duration_ms": r.duration_ms,
                "step_results": [
                    {
                        "id": sr.id,
                        "step_id": sr.step_id,
                        "status": sr.status,
                        "comment": sr.comment,
                        "duration_ms": sr.duration_ms,
                        "log_output": sr.log_output,
                    }
                    for sr in step_results_by_result.get(r.id, [])
                ],
                "attachments": _attachment_dicts(
                    result_attachments_by_result.get(r.id, []),
                    files,
                    f"attachments/results/{r.id}",
                ),
            }
            for r in results
        ],
    }


def _attachment_dicts(items, files: list[tuple[str, str]], prefix: str) -> list[dict]:
    out = []
    for a in items:
        archive_name = f"{prefix}/{a.filename}"
        if a.file_path:
            files.append((archive_name, a.file_path))
        out.append({
            "id": a.id,
            "filename": a.filename,
            "content_type": a.content_type,
            "size_bytes": a.size_bytes,
            "uploaded_at": a.uploaded_at,
            "archive_path": archive_name,
        })
    return out


def _group_by(items, key):
    out: dict = {}
    for item in items:
        out.setdefault(key(item), []).append(item)
    return out


def _safe_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name.lower())
    return cleaned.strip("-") or "project"


def _app_version() -> str:
    try:
        return version("testjam-api")
    except PackageNotFoundError:
        return "unknown"


def cleanup_archive(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
