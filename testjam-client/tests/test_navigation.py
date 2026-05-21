"""Recursive helpers: suite trees, parent chains, dotted paths."""


def _seed_tree(auth_client) -> dict:
    project = auth_client.projects.find_or_create("Tree")
    root = auth_client.suites.find_or_create(project["id"], "root")
    a = auth_client.suites.find_or_create(project["id"], "A", parent_suite_id=root["id"])
    b = auth_client.suites.find_or_create(project["id"], "B", parent_suite_id=a["id"])
    c = auth_client.suites.find_or_create(project["id"], "C", parent_suite_id=b["id"])

    case_root = auth_client.cases.find_or_create(root["id"], "case-root")
    case_a = auth_client.cases.find_or_create(a["id"], "case-a")
    case_c = auth_client.cases.find_or_create(c["id"], "case-c")

    return {
        "project": project,
        "root": root, "a": a, "b": b, "c": c,
        "case_root": case_root, "case_a": case_a, "case_c": case_c,
    }


def test_descendants_returns_every_subsuite(auth_client):
    tree = _seed_tree(auth_client)

    descendants = auth_client.suites.descendants(tree["project"]["id"], tree["root"]["id"])

    names = {s["name"] for s in descendants}
    assert names == {"A", "B", "C"}


def test_case_ids_recursive_collects_all_cases(auth_client):
    tree = _seed_tree(auth_client)

    case_ids = auth_client.suites.case_ids_recursive(
        tree["project"]["id"], tree["root"]["id"],
    )

    expected = {tree["case_root"]["id"], tree["case_a"]["id"], tree["case_c"]["id"]}
    assert set(case_ids) == expected


def test_parent_chain_returns_root_to_leaf(auth_client):
    tree = _seed_tree(auth_client)

    chain = auth_client.suites.parent_chain(tree["project"]["id"], tree["c"]["id"])

    assert [s["name"] for s in chain] == ["root", "A", "B", "C"]


def test_suites_path_dotted(auth_client):
    tree = _seed_tree(auth_client)

    path = auth_client.suites.path(tree["project"]["id"], tree["c"]["id"])

    assert path == "root.A.B.C"


def test_case_path_includes_case_name(auth_client):
    tree = _seed_tree(auth_client)

    path = auth_client.cases.path(tree["case_c"]["id"])

    assert path == "root.A.B.C.case-c"


def test_case_parent_chain(auth_client):
    tree = _seed_tree(auth_client)

    chain = auth_client.cases.parent_chain(tree["case_c"]["id"])

    assert [s["name"] for s in chain] == ["root", "A", "B", "C"]
