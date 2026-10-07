"""Application entry point: Creates the FastAPI app and registers routers.

Run with: uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers models so create_all sees them)
from app.config import settings
from app.database import Base, engine
from app.exceptions import register_exception_handlers
from app.routers import auth, tasks, users

# Descriptions shown for each endpoint group in /docs
tags_metadata = [
    {"name": "auth", "description": "Register a new account and log in to get a JWT."},
    {"name": "users", "description": "View the authenticated user's profile."},
    {
        "name": "tasks",
        "description": "Create, read, update, and delete your own tasks, "
        "plus a placeholder AI suggestion endpoint.",
    },
    {"name": "health", "description": "Check that the API is running."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup. Nothing to clean up on shutdown."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "A task management API with JWT authentication. "
        "Each user can only see and manage their own tasks."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# Allow the Streamlit frontend (Default Port 8501) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/", tags=["health"])
def root():
    """Health check confirming the API is running."""
    return {"message": f"Welcome to {settings.app_name}"}