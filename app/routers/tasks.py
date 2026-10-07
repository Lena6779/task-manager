"""Task CRUD endpoints. Every route requires authentication; accessing
another user's task returns 403."""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Priority, Task, User
from app.schemas import (
    SuggestRequest,
    TaskCreate,
    TaskResponse,
    TaskSuggestion,
    TaskUpdate,
)
from app.utils.auth import get_current_user
from app.utils.background import log_activity
from app.utils.helpers import get_owned_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


# "" instead of "/" so the URL is exactly /tasks with no trailing slash
@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a task owned by the authenticated user."""
    task = Task(**task_in.model_dump(), user_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(
        log_activity, current_user.id, "created_task", f"task_id={task.id}"
    )
    return task


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    completed: bool | None = None,
    priority: Priority | None = None,
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max tasks to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the authenticated user's tasks.

    Optional filters: ``completed`` and ``priority``.
    Pagination: ``skip`` and ``limit`` (max 100).
    """
    # Always scope to the current user first
    query = select(Task).where(Task.user_id == current_user.id)
    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority is not None:
        query = query.where(Task.priority == priority)
    # Stable ordering keeps pagination consistent between requests
    query = query.order_by(Task.id).offset(skip).limit(limit)
    return db.scalars(query).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one task. Returns 404 if it doesn't exist, 403 if it isn't yours."""
    return get_owned_task(db, task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update a task. Only fields included in the body change."""
    task = get_owned_task(db, task_id, current_user.id)
    changes = task_in.model_dump(exclude_unset=True)
    # exclude_unset skips fields the client didn't send, so they stay as-is
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(
        log_activity,
        current_user.id,
        "updated_task",
        f"task_id={task.id} fields={list(changes)}",
    )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a task. Returns 204 with no body on success."""
    task = get_owned_task(db, task_id, current_user.id)
    db.delete(task)
    db.commit()

    background_tasks.add_task(
        log_activity, current_user.id, "deleted_task", f"task_id={task_id}"
    )


@router.post("/{task_id}/suggest", response_model=TaskSuggestion)
def suggest_for_task(
    task_id: int,
    payload: SuggestRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a task description and return a placeholder AI suggestion.

    Send a ``description`` in the body, or omit the body to use the
    task's saved description. No real AI service is called yet.
    """
    task = get_owned_task(db, task_id, current_user.id)

    # Priority: description from the request, then the saved one, then the title
    if payload and payload.description:
        description = payload.description
    else:
        description = task.description or task.title

    # TODO: replace with a real AI call that sends `description`
    suggestion = (
        f"Suggested next steps for '{task.title}': "
        f"break it into smaller steps, start with the first one today, "
        f"and since it's {task.priority.value} priority, schedule time for it accordingly."
    )

    return TaskSuggestion(
        task_id=task.id,
        description=description,
        suggestion=suggestion,
    )