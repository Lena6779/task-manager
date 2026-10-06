def test_register_returns_token(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_register_duplicate_email_fails(client):
    user = {"email": "dup@example.com", "password": "password123"}
    client.post("/auth/register", json=user)
    response = client.post("/auth/register", json=user)
    assert response.status_code == 400


def test_register_short_password_fails(client):
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert response.status_code == 422


def test_login_returns_token(client):
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )
    response = client.post(
        "/auth/token",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "password123"},
    )
    response = client.post(
        "/auth/token",
        data={"username": "wrong@example.com", "password": "notmypassword"},
    )
    assert response.status_code == 401


def test_get_me(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user1@example.com"
    assert "hashed_password" not in response.json()


def test_get_me_without_token_fails(client):
    response = client.get("/users/me")
    assert response.status_code == 401