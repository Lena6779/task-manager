"""Tests for registration, login, and the /users/me endpoint."""


def register(client, email="new@example.com", password="password123", name="New User"):
    """Register a user and return the response."""
    return client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def test_register_returns_token(client):
    response = register(client)
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_register_duplicate_email_returns_409(client):
    register(client, email="dup@example.com")
    response = register(client, email="dup@example.com")
    assert response.status_code == 409
    assert response.json()["error"] == "Duplicate"


def test_register_short_password_fails(client):
    response = register(client, password="123")
    assert response.status_code == 422
    assert response.json()["error"] == "ValidationError"


def test_register_missing_name_fails(client):
    response = client.post(
        "/auth/register",
        json={"email": "noname@example.com", "password": "password123"},
    )
    assert response.status_code == 422


def test_login_returns_token(client):
    register(client, email="login@example.com")
    response = client.post(
        "/auth/token",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_fails(client):
    register(client, email="wrong@example.com")
    response = client.post(
        "/auth/token",
        data={"username": "wrong@example.com", "password": "notmypassword"},
    )
    assert response.status_code == 401


def test_get_me(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user1@example.com"
    assert data["name"] == "User One"
    assert data["is_active"] is True
    assert "hashed_password" not in data
    assert "password" not in data


def test_get_me_without_token_fails(client):
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["status_code"] == 401