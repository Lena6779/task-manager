"""Shared helper functions for routers."""

from sqlalchemy.orm import Session

from app.exceptions import ForbiddenException, NotFoundException
from app.models import Task


def get_owned_task(db: Session, task_id: int, user_id: int) -> Task:
    """Fetch a task and confirm it belongs to the given user.

    Raises:
        NotFoundException: 404 if no task has this id.
        ForbiddenException: 403 if the task belongs to another user.
    """
    task = db.get(Task, task_id)
    if task is None:
        raise NotFoundException(f"Task {task_id} not found")
    if task.user_id != user_id:
        raise ForbiddenException("You do not have access to this task")
    return task