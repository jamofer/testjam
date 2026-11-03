import pytest

JUNIT_REPORT = b"""<?xml version="1.0"?>
<testsuite name="ci"><testcase name="Login"><failure message="boom"/></testcase></testsuite>"""

ROBOT_REPORT = b"""<?xml version="1.0" encoding="UTF-8"?>
<robot generator="Robot 7"><suite name="Smoke">
<test name="Login"><status status="PASS"/></test>
</suite></robot>"""


@pytest.fixture
def project(auth_client):
    return auth_client.projects.find_or_create("Workflows")


@pytest.fixture
def case(auth_client, project):
    suite = auth_client.suites.find_or_create(project["id"], "Smoke")
    return auth_client.cases.find_or_create(suite["id"], "Login")


@pytest.fixture
def execution(auth_client, project, case):
    return auth_client.executions.create(
        project["id"], title="Nightly", type="automatic", test_case_ids=[case["id"]],
    )


@pytest.fixture
def result(auth_client, execution):
    return auth_client.executions.list_results(execution["id"])[0]


def test_bulk_results_updates_existing_results(auth_client, execution, case):
    response = auth_client.executions.bulk_results(
        execution["id"], [{"test_case_id": case["id"], "status": "passed"}],
    )

    assert (response["created"], response["updated"]) == (0, 1)
    assert auth_client.executions.list_results(execution["id"])[0]["status"] == "passed"


def test_reopen_returns_a_closed_execution_to_progress(auth_client, execution):
    auth_client.executions.update(execution["id"], status="completed")

    reopened = auth_client.executions.reopen(execution["id"])

    assert reopened["status"] == "in_progress"


def test_import_junit_applies_the_report(auth_client, execution):
    auth_client.executions.import_junit(execution["id"], filename="junit.xml", content=JUNIT_REPORT)

    assert auth_client.executions.list_results(execution["id"])[0]["status"] == "failed"


def test_import_robotframework_applies_the_report(auth_client, execution):
    auth_client.executions.import_robotframework(execution["id"], filename="output.xml", content=ROBOT_REPORT)

    assert auth_client.executions.list_results(execution["id"])[0]["status"] == "passed"


def test_exports_return_the_report_files(auth_client, execution):
    workbook = auth_client.executions.export_xlsx(execution["id"])
    report = auth_client.executions.export_html(execution["id"])

    assert workbook.startswith(b"PK")
    assert "<html" in report.lower()


def test_result_attachments_round_trip(auth_client, result):
    uploaded = auth_client.results.upload_attachment(
        result["id"], filename="screen.png", content=b"\x89PNG", mime="image/png",
    )

    listed = auth_client.results.list_attachments(result["id"])

    assert [attachment["id"] for attachment in listed] == [uploaded["id"]]


def test_execution_attachments_are_listed(auth_client, execution):
    uploaded = auth_client.executions.upload_attachment(
        execution["id"], filename="log.txt", content=b"log", mime="text/plain",
    )

    listed = auth_client.executions.list_attachments(execution["id"])

    assert [attachment["id"] for attachment in listed] == [uploaded["id"]]
