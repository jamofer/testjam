def test_create_user(auth_client):
    resp = auth_client.post("/api/v1/users", json={
        "username": "newuser", "email": "new@example.com", "password": "pass123",
    })

    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


def test_create_user_duplicate_username(auth_client):
    auth_client.post("/api/v1/users", json={"username": "dup", "email": "a@x.com", "password": "pw"})

    resp = auth_client.post("/api/v1/users", json={"username": "dup", "email": "b@x.com", "password": "pw"})

    assert resp.status_code == 400


def test_get_user_by_id(auth_client):
    user_id = auth_client.post("/api/v1/users", json={
        "username": "getme", "email": "g@x.com", "password": "pw",
    }).json()["id"]

    resp = auth_client.get(f"/api/v1/users/{user_id}")

    assert resp.status_code == 200
    assert resp.json()["username"] == "getme"


def test_get_user_not_found(auth_client):
    resp = auth_client.get("/api/v1/users/99999")

    assert resp.status_code == 404


def test_update_user(auth_client):
    user_id = auth_client.post("/api/v1/users", json={
        "username": "upd", "email": "upd@x.com", "password": "pw",
    }).json()["id"]

    resp = auth_client.put(f"/api/v1/users/{user_id}", json={"full_name": "Updated Name"})

    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


def test_delete_user(auth_client):
    user_id = auth_client.post("/api/v1/users", json={
        "username": "del", "email": "del@x.com", "password": "pw",
    }).json()["id"]

    resp = auth_client.delete(f"/api/v1/users/{user_id}")

    assert resp.status_code == 204
    listed_ids = {u["id"] for u in auth_client.get("/api/v1/users").json()}
    assert user_id not in listed_ids


def test_list_users(auth_client):
    auth_client.post("/api/v1/users", json={"username": "a", "email": "a@x.com", "password": "pw"})
    auth_client.post("/api/v1/users", json={"username": "b", "email": "b@x.com", "password": "pw"})

    resp = auth_client.get("/api/v1/users")

    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "a" in usernames
    assert "b" in usernames
