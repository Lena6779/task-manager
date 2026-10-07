# Task Manager API

A task management REST API built with FastAPI. Users register, log in with a JWT, and manage their own tasks. Every task endpoint is protected, and users can only access tasks they own.

## Features

- **JWT authentication** with expiring tokens and bcrypt password hashing
- **Task CRUD** with filtering by `completed` and `priority`, plus pagination
- **Ownership rules**: accessing another user's task returns `403 Forbidden`
- **AI-ready endpoint** that returns a placeholder suggestion for a task
- **Background task** that logs user activity to `activity.log`
- **Consistent JSON error format** via custom exceptions and global handlers
- **CORS** configured for a frontend at `localhost:8501`
- **Interactive docs** at `/docs` (Swagger UI) and `/redoc`

## Tech Stack

FastAPI · SQLAlchemy · SQLite · Pydantic · PyJWT · bcrypt · pytest

## Project Structure

```
task-manager/
├── app/
│   ├── main.py            # App setup, metadata, CORS, routers
│   ├── config.py          # Settings loaded from .env
│   ├── database.py        # Engine, sessions, get_db dependency
│   ├── exceptions.py      # Custom exceptions and global handlers
│   ├── models/            # SQLAlchemy models (User, Task)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/           # Endpoints: auth, users, tasks
│   └── utils/             # Auth helpers, ownership check, background tasks
├── tests/                 # pytest suite
├── requirements.txt
└── pytest.ini
```

## Setup

**1. Clone the repo and create a virtual environment**

```bash
git clone https://github.com/Lena6779/task-manager.git
cd task-manager
python -m venv venv
```

Activate it:

- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- macOS/Linux: `source venv/bin/activate`

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Create a `.env` file** in the project root:

```
APP_NAME=Task Manager
DATABASE_URL=sqlite:///./tasks.db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secure `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The app will not start without `SECRET_KEY`. Never commit `.env` to version control.

## Running the App

```bash
uvicorn app.main:app --reload
```

The database tables are created automatically on startup.

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Logging in through `/docs`

1. Call `POST /auth/register` with a name, email, and password (8+ characters).
2. Click the **Authorize** button at the top of the page.
3. Enter your **email** in the `username` field, plus your password, and click Authorize.
4. All protected endpoints now send your token automatically.

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Create a user and return a JWT | No |
| POST | `/auth/token` | Log in with email and password (form data), return a JWT | No |
| GET | `/users/me` | Get the current user's profile | Yes |

### Tasks

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/tasks` | Create a task | Yes |
| GET | `/tasks` | List your tasks | Yes |
| GET | `/tasks/{id}` | Get one of your tasks | Yes |
| PATCH | `/tasks/{id}` | Partially update one of your tasks | Yes |
| DELETE | `/tasks/{id}` | Delete one of your tasks | Yes |
| POST | `/tasks/{id}/suggest` | Get a placeholder AI suggestion | Yes |

**Query parameters for `GET /tasks`:**

| Parameter | Type | Description |
|---|---|---|
| `completed` | bool | Filter by completion status |
| `priority` | `low` / `medium` / `high` | Filter by priority |
| `skip` | int | Number of tasks to skip (default 0) |
| `limit` | int | Max tasks to return (default 100, max 100) |

Example: `GET /tasks?priority=high&completed=false&limit=10`

**`POST /tasks/{id}/suggest`** accepts an optional body with a `description`. If no body is sent, it uses the task's saved description. The response is placeholder text marked with `"is_placeholder": true`, ready to be swapped for a real AI service later.

## Data Models

**User**: `id`, `name`, `email` (unique), `hashed_password`, `is_active`, `created_at`

**Task**: `id`, `title` (1–200 chars), `description` (up to 2000 chars), `priority` (`low` / `medium` / `high`), `completed`, `user_id` (foreign key), `created_at`, `updated_at`

Passwords are stored only as bcrypt hashes and never appear in any API response.

## Error Handling

All errors return the same JSON shape:

```json
{
  "error": "NotFound",
  "message": "Task 5 not found",
  "status_code": 404
}
```

| Status | Error | When |
|---|---|---|
| 401 | `HTTPError` | Missing, invalid, or expired token; wrong login credentials |
| 403 | `Forbidden` | Accessing another user's task, or an inactive account |
| 404 | `NotFound` | Task does not exist |
| 409 | `Duplicate` | Registering with an email that's already in use |
| 422 | `ValidationError` | Invalid request data (includes a `details` list) |

## Background Tasks

Registering, creating, updating, and deleting tasks are logged to `activity.log` using FastAPI's `BackgroundTasks`. The log is written after the response is sent, so it doesn't slow down requests.

## Running Tests

```bash
pytest -v
```

Tests use a separate in-memory SQLite database, so they never touch `tasks.db`. The suite covers registration and login, authentication requirements, all task endpoints, filters and pagination, ownership (403) rules, validation errors, and the error response format.