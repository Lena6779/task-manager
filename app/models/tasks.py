"""SQLAlchemy model and priority enum for tasks."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Priority(str, PyEnum):
    """Allowed task priority levels."""

    low = "low"
    medium = "medium"
    high = "high"


class Task(Base):
    """A to-do item that belongs to exactly one user."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000), default=None)
    # The database column only accepts values from the Priority enum
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority"), default=Priority.medium
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # Links each task to its owner; indexed because most queries filter on it
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # onupdate refreshes this timestamp automatically on every change
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )