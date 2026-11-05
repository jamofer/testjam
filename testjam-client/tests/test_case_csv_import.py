import pytest

CASES_CSV = (
    "suite,name,tags,steps\n"
    'Checkout / Payments,Pay with card,smoke,"Open the cart\nPay"\n'
    ",,smoke,\n"
).encode()


@pytest.fixture
def project(auth_client):
    return auth_client.projects.create("Csv Project")


def test_import_csv_reports_created_cases_and_suites(auth_client, project):
    report = auth_client.cases.import_csv(project["id"], filename="cases.csv", content=CASES_CSV)

    assert report["created"] == 1
    assert report["suites_created"] == 2


def test_import_csv_reports_row_errors(auth_client, project):
    report = auth_client.cases.import_csv(project["id"], filename="cases.csv", content=CASES_CSV)

    assert [error["row"] for error in report["errors"]] == [3]


def test_import_csv_creates_steps(auth_client, project):
    auth_client.cases.import_csv(project["id"], filename="cases.csv", content=CASES_CSV)

    [payments] = [suite for suite in auth_client.suites.list(project["id"], all=True) if suite["name"] == "Payments"]
    [case] = auth_client.cases.list(payments["id"])
    actions = [step["action"] for step in auth_client.cases.list_steps(case["id"])]
    assert actions == ["Open the cart", "Pay"]
