import pytest

FULL_CSV = (
    "suite,name,description,preconditions,tags,external_id,steps,expected\n"
    'Checkout / Payments,Pay by card,Card flow,Logged in,"smoke, payments",TC-1,'
    '"Open cart\nPay with card","Cart shows items\nOrder confirmed"\n'
)


@pytest.fixture
def import_csv(auth_client, project_id):
    def upload(content: str | bytes, client=None):
        payload = content.encode() if isinstance(content, str) else content
        return (client or auth_client).post(
            f"/api/v1/projects/{project_id}/cases/import/csv",
            files={"file": ("cases.csv", payload, "text/csv")},
        )
    return upload


@pytest.fixture
def suites_by_name(auth_client, project_id):
    def collect():
        suites = auth_client.get(f"/api/v1/projects/{project_id}/suites", params={"all": True}).json()
        return {suite["name"]: suite for suite in suites}
    return collect


def test_import_creates_the_case_with_every_column(auth_client, project_id, import_csv):
    response = import_csv(FULL_CSV)

    assert response.status_code == 200
    assert response.json() == {"created": 1, "suites_created": 2, "errors": []}
    case = auth_client.get(f"/api/v1/projects/{project_id}/cases").json()[0]
    assert case["name"] == "Pay by card"
    assert case["description"] == "Card flow"
    assert case["preconditions"] == "Logged in"
    assert case["tags"] == ["smoke", "payments"]
    assert case["external_id"] == "TC-1"


def test_import_pairs_steps_with_expected_results(auth_client, project_id, import_csv):
    import_csv(FULL_CSV)

    case = auth_client.get(f"/api/v1/projects/{project_id}/cases").json()[0]
    steps = auth_client.get(f"/api/v1/cases/{case['id']}").json()["steps"]
    assert [(step["action"], step["expected_result"]) for step in steps] == [
        ("Open cart", "Cart shows items"),
        ("Pay with card", "Order confirmed"),
    ]


def test_import_nests_suites_from_the_path(import_csv, suites_by_name):
    import_csv(FULL_CSV)

    suites = suites_by_name()
    assert suites["Payments"]["parent_suite_id"] == suites["Checkout"]["id"]


def test_import_reuses_existing_suites(auth_client, project_id, import_csv):
    auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "Checkout"})

    response = import_csv(FULL_CSV)

    suites = auth_client.get(f"/api/v1/projects/{project_id}/suites", params={"all": True}).json()
    assert response.json()["suites_created"] == 1
    assert [suite["name"] for suite in suites].count("Checkout") == 1


def test_import_puts_rows_without_suite_in_a_default_suite(import_csv, suites_by_name):
    import_csv("name\nLogin\n")

    assert "Imported" in suites_by_name()


def test_import_reports_rows_without_name(import_csv):
    response = import_csv("name,description\n,orphan\nLogin,ok\n")

    assert response.json()["created"] == 1
    assert response.json()["errors"] == [{"row": 2, "name": "", "error": "Name is empty"}]


def test_import_skips_cases_that_already_exist(import_csv):
    import_csv("suite,name\nAuth,Login\n")

    response = import_csv("suite,name\nAuth,Login\nAuth,Logout\n")

    assert response.json()["created"] == 1
    assert response.json()["errors"][0]["row"] == 2


def test_import_reads_semicolon_separated_excel_exports(auth_client, project_id, import_csv):
    content = "﻿suite;name;tags\nAuth;Inicio de sesión;smoke\n".encode("cp1252", errors="ignore")

    response = import_csv(content)

    assert response.json()["created"] == 1
    assert auth_client.get(f"/api/v1/projects/{project_id}/cases").json()[0]["name"] == "Inicio de sesión"


def test_import_accepts_title_as_the_name_column(import_csv):
    response = import_csv("Title,Section\nLogin,Auth\n")

    assert response.json()["created"] == 1


def test_import_rejects_a_csv_without_name_column(import_csv):
    response = import_csv("summary,steps\nLogin,Open\n")

    assert response.status_code == 400


@pytest.mark.parametrize(("role", "expected_status"), [("tester", 200), ("viewer", 403), ("outsider", 403)])
def test_import_requires_write_access(role_project, role, expected_status):
    response = role_project["clients"][role].post(
        f"/api/v1/projects/{role_project['project_id']}/cases/import/csv",
        files={"file": ("cases.csv", b"name\nLogin\n", "text/csv")},
    )

    assert response.status_code == expected_status
