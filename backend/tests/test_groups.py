def test_create_group(auth_client):
    resp = auth_client.post("/api/v1/groups", json={"name": "QA Team", "description": "Quality assurance"})

    assert resp.status_code == 201
    assert resp.json()["name"] == "QA Team"


def test_create_group_duplicate_name(auth_client):
    auth_client.post("/api/v1/groups", json={"name": "Unique"})

    resp = auth_client.post("/api/v1/groups", json={"name": "Unique"})

    assert resp.status_code == 400


def test_get_group(auth_client):
    group_id = auth_client.post("/api/v1/groups", json={"name": "Backend"}).json()["id"]

    resp = auth_client.get(f"/api/v1/groups/{group_id}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Backend"


def test_get_group_not_found(auth_client):
    resp = auth_client.get("/api/v1/groups/99999")

    assert resp.status_code == 404


def test_update_group(auth_client):
    group_id = auth_client.post("/api/v1/groups", json={"name": "OldName"}).json()["id"]

    resp = auth_client.put(f"/api/v1/groups/{group_id}", json={"name": "NewName"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"


def test_delete_group(auth_client):
    group_id = auth_client.post("/api/v1/groups", json={"name": "ToDelete"}).json()["id"]

    auth_client.delete(f"/api/v1/groups/{group_id}")

    assert auth_client.get(f"/api/v1/groups/{group_id}").status_code == 404


def test_list_groups(auth_client):
    auth_client.post("/api/v1/groups", json={"name": "G1"})
    auth_client.post("/api/v1/groups", json={"name": "G2"})

    resp = auth_client.get("/api/v1/groups")

    names = [g["name"] for g in resp.json()]
    assert "G1" in names and "G2" in names


def test_add_member_to_group(auth_client):
    group_id = auth_client.post("/api/v1/groups", json={"name": "G"}).json()["id"]
    user_id = auth_client.post("/api/v1/users", json={
        "username": "member", "email": "m@x.com", "password": "pw",
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/groups/{group_id}/members?user_id={user_id}&role=member")

    assert resp.status_code == 201
    members = auth_client.get(f"/api/v1/groups/{group_id}/members").json()
    assert any(m["user_id"] == user_id for m in members)


def test_add_duplicate_member_rejected(auth_client):
    group_id = auth_client.post("/api/v1/groups", json={"name": "G"}).json()["id"]
    user_id = auth_client.post("/api/v1/users", json={
        "username": "m2", "email": "m2@x.com", "password": "pw",
    }).json()["id"]
    auth_client.post(f"/api/v1/groups/{group_id}/members?user_id={user_id}&role=member")

    resp = auth_client.post(f"/api/v1/groups/{group_id}/members?user_id={user_id}&role=member")

    assert resp.status_code == 400


def test_remove_member_from_group(auth_client):
    group_id = auth_client.post("/api/v1/groups", json={"name": "G"}).json()["id"]
    user_id = auth_client.post("/api/v1/users", json={
        "username": "mr", "email": "mr@x.com", "password": "pw",
    }).json()["id"]
    auth_client.post(f"/api/v1/groups/{group_id}/members?user_id={user_id}&role=member")

    auth_client.delete(f"/api/v1/groups/{group_id}/members/{user_id}")

    members = auth_client.get(f"/api/v1/groups/{group_id}/members").json()
    assert not any(m["user_id"] == user_id for m in members)
