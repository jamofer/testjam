def test_me_returns_the_authenticated_user(auth_client):
    me = auth_client.users.me()

    assert me["username"] == "u"
    assert me["is_admin"] is True
