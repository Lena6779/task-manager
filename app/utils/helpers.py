from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task


def get_user_task_or_404(db: Session, task_id: int, user_id: int) -> Task:
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == user_id)
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task