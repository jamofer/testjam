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


def test_get_user_by_username(auth_client):
    created = auth_client.post(
        "/api/v1/users",
        json={"username": "alice", "email": "alice@x.com", "password": "pw"},
    ).json()

    resp = auth_client.get("/api/v1/users/by-username/alice")

    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["username"] == "alice"


def test_get_user_by_username_not_found(auth_client):
    resp = auth_client.get("/api/v1/users/by-username/ghost")

    assert resp.status_code == 404


def test_user_cannot_change_administrative_fields_of_own_account(auth_client):
    auth_client.put("/api/v1/users/me", json={"is_active": False, "failed_login_count": 0})

    response = auth_client.get("/api/v1/users/me")

    assert response.json()["is_active"] is True


def test_password_cannot_be_changed_through_profile_update(auth_client):
    response = auth_client.put("/api/v1/users/me", json={"password": "changed-password"})

    assert response.status_code == 200
    assert "password" not in response.json()


def test_email_of_another_user_is_rejected(auth_client):
    auth_client.post(
        "/api/v1/users", json={"username": "other", "email": "other@test.com", "password": "pw"},
    )

    response = auth_client.put("/api/v1/users/me", json={"email": "other@test.com"})

    assert response.status_code == 400


def test_keeping_own_email_is_accepted(auth_client):
    email = auth_client.get("/api/v1/users/me").json()["email"]

    response = auth_client.put("/api/v1/users/me", json={"email": email})

    assert response.status_code == 200


def test_creating_user_with_taken_email_is_rejected(auth_client):
    email = auth_client.get("/api/v1/users/me").json()["email"]

    response = auth_client.post(
        "/api/v1/users", json={"username": "copycat", "email": email, "password": "pw"},
    )

    assert response.status_code == 400


def test_admin_cannot_assign_taken_email(auth_client):
    email = auth_client.get("/api/v1/users/me").json()["email"]
    user_id = auth_client.post(
        "/api/v1/users", json={"username": "other", "email": "other@test.com", "password": "pw"},
    ).json()["id"]

    response = auth_client.put(f"/api/v1/users/{user_id}", json={"email": email})

    assert response.status_code == 409
