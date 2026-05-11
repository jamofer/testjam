"""Shared helpers used across execution submodules."""
from sqlalchemy.orm import Session, selectinload

from testjam.models.execution import ExecutionAttachment, TestExecution, TestResult
from testjam.schemas.execution import ExecutionAttachmentOut, ExecutionSummary, TestExecutionOut


def compute_summary(execution: TestExecution) -> ExecutionSummary:
    counts = {"passed": 0, "failed": 0, "blocked": 0, "not_run": 0}
    for r in execution.results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return ExecutionSummary(total=len(execution.results), **counts)


def execution_out(ex: TestExecution) -> TestExecutionOut:
    data = TestExecutionOut.model_validate(ex)
    data.summary = compute_summary(ex)
    data.attachments = [ExecutionAttachmentOut.model_validate(a) for a in ex.attachments]
    return data


def load_execution_full(db: Session, ex_id: int) -> TestExecution | None:
    """Eager-load relationships used by `execution_out` and the xlsx export
    to avoid N+1 lazy queries on results / step_results / attachments / test_case."""
    return (
        db.query(TestExecution)
        .options(
            selectinload(TestExecution.results).selectinload(TestResult.test_case),
            selectinload(TestExecution.results).selectinload(TestResult.step_results),
            selectinload(TestExecution.results).selectinload(TestResult.attachments),
            selectinload(TestExecution.attachments),
        )
        .filter(TestExecution.id == ex_id)
        .first()
    )
