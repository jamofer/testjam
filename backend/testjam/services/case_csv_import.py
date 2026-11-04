"""Create test cases (and their suites) from a CSV file, one row per case."""
import csv
import io
import re
from dataclasses import dataclass, field

from fastapi import HTTPException
from sqlalchemy.orm import Session

from testjam.models.testcase import TestCase, TestStep, TestSuite
from testjam.models.user import User
from testjam.services import custom_fields as custom_field_service
from testjam.services.case_revisions import write_revision

DEFAULT_SUITE_NAME = "Imported"
SUITE_PATH_SEPARATOR = "/"
TAG_SEPARATORS = re.compile(r"[,;]")
CANDIDATE_DELIMITERS = ",;\t"
SNIFF_SAMPLE_CHARS = 4096
FIRST_DATA_ROW = 2
MAX_NAME_LENGTH = 255
COLUMN_ALIASES = {
    "name": "name",
    "title": "name",
    "suite": "suite",
    "section": "suite",
    "description": "description",
    "preconditions": "preconditions",
    "tags": "tags",
    "external_id": "external_id",
    "steps": "steps",
    "expected": "expected",
    "expected_result": "expected",
    "expected_results": "expected",
}

MISSING_NAME_COLUMN = "The CSV needs a 'name' column"
UNREADABLE_FILE = "The file is not a readable CSV"
MISSING_NAME = "Name is empty"
NAME_TOO_LONG = f"Name is longer than {MAX_NAME_LENGTH} characters"
DUPLICATE_CASE = "A test case with this name already exists in the suite"


@dataclass
class ImportReport:
    created: int = 0
    suites_created: int = 0
    errors: list[dict] = field(default_factory=list)


def import_cases(db: Session, project_id: int, payload: bytes, actor: User) -> ImportReport:
    rows = _read_rows(payload)
    report = ImportReport()
    suites = _SuiteResolver(db, project_id, report)
    for row_number, row in enumerate(rows, start=FIRST_DATA_ROW):
        error = _row_error(row)
        if error is None:
            error = _create_case(db, project_id, suites.resolve(row.get("suite", "")), row, actor)
        if error is None:
            report.created += 1
        else:
            report.errors.append({"row": row_number, "name": row.get("name", ""), "error": error})
    return report


class _SuiteResolver:
    """Find or create the suite for a `Parent / Child` path, caching each level."""

    def __init__(self, db: Session, project_id: int, report: ImportReport) -> None:
        self._db = db
        self._project_id = project_id
        self._report = report
        self._cache: dict[tuple[int | None, str], TestSuite] = {}

    def resolve(self, path: str) -> TestSuite:
        names = [part.strip() for part in path.split(SUITE_PATH_SEPARATOR) if part.strip()]
        parent: TestSuite | None = None
        for name in names or [DEFAULT_SUITE_NAME]:
            parent = self._child(parent, name)
        return parent

    def _child(self, parent: TestSuite | None, name: str) -> TestSuite:
        parent_id = parent.id if parent else None
        key = (parent_id, name)
        if key not in self._cache:
            self._cache[key] = self._find(parent_id, name) or self._create(parent_id, name)
        return self._cache[key]

    def _find(self, parent_id: int | None, name: str) -> TestSuite | None:
        return (
            self._db.query(TestSuite)
            .filter(
                TestSuite.project_id == self._project_id,
                TestSuite.parent_suite_id == parent_id,
                TestSuite.name == name,
            )
            .first()
        )

    def _create(self, parent_id: int | None, name: str) -> TestSuite:
        siblings = (
            self._db.query(TestSuite)
            .filter(TestSuite.project_id == self._project_id, TestSuite.parent_suite_id == parent_id)
            .count()
        )
        suite = TestSuite(
            project_id=self._project_id, parent_suite_id=parent_id, name=name, order=siblings + 1,
        )
        self._db.add(suite)
        self._db.flush()
        self._report.suites_created += 1
        return suite


def _read_rows(payload: bytes) -> list[dict[str, str]]:
    text = _decode(payload)
    try:
        reader = csv.DictReader(io.StringIO(text), dialect=_dialect(text))
        header = reader.fieldnames or []
        rows = list(reader)
    except csv.Error as error:
        raise HTTPException(status_code=400, detail=UNREADABLE_FILE) from error
    columns = {name: COLUMN_ALIASES.get(name.strip().lower()) for name in header if name}
    if "name" not in columns.values():
        raise HTTPException(status_code=400, detail=MISSING_NAME_COLUMN)
    return [_normalize_row(row, columns) for row in rows if any((value or "").strip() for value in row.values())]


def _dialect(text: str) -> type[csv.Dialect]:
    header = text[:SNIFF_SAMPLE_CHARS].splitlines()[0] if text.strip() else ""
    try:
        return csv.Sniffer().sniff(header, delimiters=CANDIDATE_DELIMITERS)
    except csv.Error:
        return csv.excel


def _decode(payload: bytes) -> str:
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return payload.decode("cp1252", errors="replace")


def _normalize_row(row: dict, columns: dict[str, str | None]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for header, column in columns.items():
        if column and column not in normalized:
            normalized[column] = (row.get(header) or "").strip()
    return normalized


def _row_error(row: dict[str, str]) -> str | None:
    name = row.get("name", "")
    if not name:
        return MISSING_NAME
    if len(name) > MAX_NAME_LENGTH:
        return NAME_TOO_LONG
    return None


def _create_case(db: Session, project_id: int, suite: TestSuite, row: dict[str, str], actor: User) -> str | None:
    if _has_duplicate(db, suite, row["name"]):
        return DUPLICATE_CASE
    try:
        case_custom_fields = custom_field_service.validate_payload(
            db, project_id, "test_case", None, is_create=True,
        )
    except HTTPException as error:
        return str(error.detail)
    siblings = db.query(TestCase).filter(TestCase.suite_id == suite.id).count()
    case = TestCase(
        suite_id=suite.id,
        name=row["name"],
        description=row.get("description") or None,
        preconditions=row.get("preconditions") or None,
        tags=_tags(row.get("tags", "")),
        external_id=row.get("external_id") or None,
        custom_fields=case_custom_fields,
        order=siblings + 1,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(case)
    db.flush()
    for step in _steps(row.get("steps", ""), row.get("expected", "")):
        step.test_case_id = case.id
        db.add(step)
    db.flush()
    db.refresh(case)
    write_revision(db, case, actor, "created")
    return None


def _has_duplicate(db: Session, suite: TestSuite, name: str) -> bool:
    return db.query(TestCase.id).filter(TestCase.suite_id == suite.id, TestCase.name == name).first() is not None


def _tags(raw: str) -> list[str] | None:
    tags = [tag.strip() for tag in TAG_SEPARATORS.split(raw) if tag.strip()]
    return tags or None


def _steps(raw_actions: str, raw_expected: str) -> list[TestStep]:
    actions = _lines(raw_actions)
    expected = _lines(raw_expected)
    return [
        TestStep(
            order=position,
            step_type="action",
            action=action,
            expected_result=expected[position - 1] if position <= len(expected) else None,
        )
        for position, action in enumerate(actions, start=1)
    ]


def _lines(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]
