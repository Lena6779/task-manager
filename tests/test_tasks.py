def create_task(client, headers, **fields):
    """Helper so each test can create a task in one line."""
    body = {"title": "Test task", **fields}
    return client.post("/tasks", json=body, headers=headers)


# ---------- CREATE ----------

def test_create_task(client, auth_headers):
    response = create_task(client, auth_headers, title="Buy milk")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is False
    assert data["priority"] == "medium"


def test_create_task_requires_auth(client):
    response = client.post("/tasks", json={"title": "No token"})
    assert response.status_code == 401


def test_create_task_empty_title_fails(client, auth_headers):
    response = create_task(client, auth_headers, title="")
    assert response.status_code == 422


def test_create_task_invalid_priority_fails(client, auth_headers):
    response = create_task(client, auth_headers, priority="urgent")
    assert response.status_code == 422


# ---------- LIST ----------

def test_list_only_shows_own_tasks(client, auth_headers, other_auth_headers):
    create_task(client, auth_headers, title="Mine")
    create_task(client, other_auth_headers, title="Theirs")
    response = client.get("/tasks", headers=auth_headers)
    titles = [t["title"] for t in response.json()]
    assert titles == ["Mine"]


def test_filter_by_completed(client, auth_headers):
    task_id = create_task(client, auth_headers, title="Done").json()["id"]
    create_task(client, auth_headers, title="Not done")
    client.patch(f"/tasks/{task_id}", json={"completed": True}, headers=auth_headers)

    response = client.get("/tasks?completed=true", headers=auth_headers)
    titles = [t["title"] for t in response.json()]
    assert titles == ["Done"]


def test_filter_by_priority(client, auth_headers):
    create_task(client, auth_headers, title="Urgent", priority="high")
    create_task(client, auth_headers, title="Later", priority="low")
    response = client.get("/tasks?priority=high", headers=auth_headers)
    titles = [t["title"] for t in response.json()]
    assert titles == ["Urgent"]


def test_pagination(client, auth_headers):
    for i in range(5):
        create_task(client, auth_headers, title=f"Task {i}")
    response = client.get("/tasks?skip=2&limit=2", headers=auth_headers)
    titles = [t["title"] for t in response.json()]
    assert titles == ["Task 2", "Task 3"]


# ---------- GET ONE ----------

def test_get_own_task(client, auth_headers):
    task_id = create_task(client, auth_headers).json()["id"]
    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200


def test_get_other_users_task_returns_404(client, auth_headers, other_auth_headers):
    task_id = create_task(client, auth_headers).json()["id"]
    response = client.get(f"/tasks/{task_id}", headers=other_auth_headers)
    assert response.status_code == 404


# ---------- UPDATE ----------

def test_partial_update(client, auth_headers):
    task_id = create_task(client, auth_headers, title="Original").json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"priority": "high"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["priority"] == "high"
    assert response.json()["title"] == "Original"  # unchanged


def test_update_other_users_task_returns_404(client, auth_headers, other_auth_headers):
    task_id = create_task(client, auth_headers).json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"title": "Hacked"}, headers=other_auth_headers
    )
    assert response.status_code == 404


# ---------- DELETE ----------

def test_delete_task(client, auth_headers):
    task_id = create_task(client, auth_headers).json()["id"]
    assert client.delete(f"/tasks/{task_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/tasks/{task_id}", headers=auth_headers).status_code == 404


def test_delete_other_users_task_returns_404(client, auth_headers, other_auth_headers):
    task_id = create_task(client, auth_headers).json()["id"]
    response = client.delete(f"/tasks/{task_id}", headers=other_auth_headers)
    assert response.status_code == 404



# ---------- SUGGEST ----------

def test_suggest_returns_placeholder(client, auth_headers):
    task_id = create_task(
        client, auth_headers, title="Write report", description="Q3 sales summary"
    ).json()["id"]
    response = client.post(f"/tasks/{task_id}/suggest", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["description"] == "Q3 sales summary"
    assert data["is_placeholder"] is True
    assert "Write report" in data["suggestion"]


def test_suggest_other_users_task_returns_404(client, auth_headers, other_auth_headers):
    task_id = create_task(client, auth_headers).json()["id"]
    response = client.post(f"/tasks/{task_id}/suggest", headers=other_auth_headers)
    assert response.status_code == 404


def test_suggest_requires_auth(client):
    response = client.post("/tasks/1/suggest")
    assert response.status_code == 401