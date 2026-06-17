def test_login_success(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "adminpass"})
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"


def test_login_wrong_password(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", json={"username": "nobody", "password": "x"})
    assert r.status_code == 401


def test_me_authenticated(client, admin_headers):
    r = client.get("/auth/me", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"
    assert r.json()["role"] == "admin"


def test_me_unauthenticated(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_bad_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert r.status_code == 401


def test_create_and_delete_user(client, admin_headers):
    # Create viewer
    r = client.post("/auth/users",
        json={"username": "testviewer", "password": "pass123", "role": "viewer"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    user_id = r.json()["id"]
    assert r.json()["role"] == "viewer"

    # Duplicate username rejected
    r2 = client.post("/auth/users",
        json={"username": "testviewer", "password": "x", "role": "viewer"},
        headers=admin_headers,
    )
    assert r2.status_code == 400

    # Delete
    r3 = client.delete(f"/auth/users/{user_id}", headers=admin_headers)
    assert r3.status_code == 200


def test_create_user_unauthorized(client):
    r = client.post("/auth/users",
        json={"username": "hacker", "password": "x", "role": "admin"},
    )
    assert r.status_code == 401


def test_update_user_password(client, admin_headers):
    r = client.post("/auth/users",
        json={"username": "pwchangeuser", "password": "oldpass", "role": "viewer"},
        headers=admin_headers,
    )
    user_id = r.json()["id"]

    r2 = client.put(f"/auth/users/{user_id}",
        json={"password": "newpass"},
        headers=admin_headers,
    )
    assert r2.status_code == 200

    # Login with new password works
    r3 = client.post("/auth/login", json={"username": "pwchangeuser", "password": "newpass"})
    assert r3.status_code == 200

    client.delete(f"/auth/users/{user_id}", headers=admin_headers)


def test_cannot_delete_last_admin(client, admin_headers):
    me = client.get("/auth/me", headers=admin_headers).json()
    r = client.delete(f"/auth/users/{me['id']}", headers=admin_headers)
    assert r.status_code == 400


def test_invalid_role_rejected(client, admin_headers):
    r = client.post("/auth/users",
        json={"username": "x", "password": "x", "role": "superadmin"},
        headers=admin_headers,
    )
    assert r.status_code == 400
