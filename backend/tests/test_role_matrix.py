"""Role boundary enforcement on project-scoped endpoints.

Catches regressions where a writer-required endpoint silently accepts
viewer or outsider credentials. Admin is excluded on purpose: admins
bypass every check, so admin coverage hides role bugs (see TG2 in
PRE-RELEASE_V1.0.md).
"""
import pytest

ALLOWED = 200
CREATED = 201
NO_CONTENT = 204
FORBIDDEN = 403

READ_ROLES = ["owner", "tester", "viewer"]
WRITE_ROLES = ["owner", "tester"]


def _ok(status_code: int) -> bool:
    return status_code in (ALLOWED, CREATED, NO_CONTENT)


@pytest.mark.parametrize("role", READ_ROLES)
@pytest.mark.parametrize("path_template", [
    "/api/v1/projects/{id}",
    "/api/v1/projects/{id}/suites",
    "/api/v1/projects/{id}/bugs",
    "/api/v1/projects/{id}/executions",
    "/api/v1/projects/{id}/versions",
])
def test_member_can_read_project_scoped_listings(role_project, role, path_template):
    project_id = role_project["project_id"]
    client = role_project["clients"][role]

    response = client.get(path_template.format(id=project_id))

    assert _ok(response.status_code), (
        f"{role} reading {path_template} got {response.status_code}: {response.text}"
    )


@pytest.mark.parametrize("path_template", [
    "/api/v1/projects/{id}",
    "/api/v1/projects/{id}/suites",
    "/api/v1/projects/{id}/bugs",
    "/api/v1/projects/{id}/executions",
    "/api/v1/projects/{id}/versions",
])
def test_outsider_cannot_read_project_scoped_listings(role_project, path_template):
    project_id = role_project["project_id"]
    client = role_project["clients"]["outsider"]

    response = client.get(path_template.format(id=project_id))

    assert response.status_code == FORBIDDEN, (
        f"outsider reading {path_template} got {response.status_code}"
    )


WRITE_CASES = [
    ("POST", "/api/v1/projects/{id}/suites", lambda ctx: {"name": f"Suite-{ctx['role']}"}),
    ("POST", "/api/v1/projects/{id}/versions", lambda ctx: {"name": f"v-{ctx['role']}"}),
    ("POST", "/api/v1/projects/{id}/bugs", lambda ctx: {"title": f"Bug-{ctx['role']}"}),
    ("POST", "/api/v1/projects/{id}/plans", lambda ctx: {"title": f"Plan-{ctx['role']}"}),
    ("POST", "/api/v1/projects/{id}/executions", lambda ctx: {
        "title": f"Run-{ctx['role']}", "type": "manual", "test_case_ids": [],
    }),
]


@pytest.mark.parametrize("role", WRITE_ROLES)
@pytest.mark.parametrize("method,path_template,payload_fn", WRITE_CASES)
def test_writer_can_mutate_project_scoped_resource(
    role_project, role, method, path_template, payload_fn,
):
    project_id = role_project["project_id"]
    client = role_project["clients"][role]

    response = client.request(
        method,
        path_template.format(id=project_id),
        json=payload_fn({"role": role}),
    )

    assert _ok(response.status_code), (
        f"{role} {method} {path_template} got {response.status_code}: {response.text}"
    )


@pytest.mark.parametrize("role", ["viewer", "outsider"])
@pytest.mark.parametrize("method,path_template,payload_fn", WRITE_CASES)
def test_non_writer_blocked_from_project_scoped_mutation(
    role_project, role, method, path_template, payload_fn,
):
    project_id = role_project["project_id"]
    client = role_project["clients"][role]

    response = client.request(
        method,
        path_template.format(id=project_id),
        json=payload_fn({"role": role}),
    )

    assert response.status_code == FORBIDDEN, (
        f"{role} {method} {path_template} got {response.status_code}: {response.text}"
    )


def test_writer_can_create_case_under_suite(role_project):
    project_id = role_project["project_id"]
    owner = role_project["clients"]["owner"]
    suite_id = owner.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]

    for role in WRITE_ROLES:
        response = role_project["clients"][role].post(
            f"/api/v1/suites/{suite_id}/cases",
            json={"name": f"TC-{role}", "suite_id": suite_id},
        )

        assert _ok(response.status_code), (
            f"{role} creating case got {response.status_code}: {response.text}"
        )


def test_non_writer_blocked_from_case_creation(role_project):
    project_id = role_project["project_id"]
    owner = role_project["clients"]["owner"]
    suite_id = owner.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]

    for role in ["viewer", "outsider"]:
        response = role_project["clients"][role].post(
            f"/api/v1/suites/{suite_id}/cases",
            json={"name": f"TC-{role}", "suite_id": suite_id},
        )

        assert response.status_code == FORBIDDEN, (
            f"{role} creating case got {response.status_code}: {response.text}"
        )


def test_writer_can_add_step_to_case(role_project):
    project_id = role_project["project_id"]
    owner = role_project["clients"]["owner"]
    suite_id = owner.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = owner.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]

    for role in WRITE_ROLES:
        response = role_project["clients"][role].post(
            f"/api/v1/cases/{case_id}/steps",
            json={"action": f"step-{role}", "order": 1},
        )

        assert _ok(response.status_code), (
            f"{role} adding step got {response.status_code}: {response.text}"
        )


def test_non_writer_blocked_from_adding_step(role_project):
    project_id = role_project["project_id"]
    owner = role_project["clients"]["owner"]
    suite_id = owner.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = owner.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]

    for role in ["viewer", "outsider"]:
        response = role_project["clients"][role].post(
            f"/api/v1/cases/{case_id}/steps",
            json={"action": f"step-{role}", "order": 1},
        )

        assert response.status_code == FORBIDDEN, (
            f"{role} adding step got {response.status_code}: {response.text}"
        )
