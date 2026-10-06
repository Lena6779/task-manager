from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.config import settings
from app.database import Base, engine
from app.routers import auth, tasks, users  # CHANGED: added auth and users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup: runs once when the server starts
    Base.metadata.create_all(bind=engine)
    yield
    # cleanup: runs once when the server stops (empty here)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CHANGED: plug in all three routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.app_name}"}