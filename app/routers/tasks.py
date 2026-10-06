from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, User
from app.schemas import TaskCreate, TaskResponse, TaskSuggestion, TaskUpdate
from app.schemas.tasks import Priority
from app.utils.auth import get_current_user
from app.utils.helpers import get_user_task_or_404

router = APIRouter(prefix="/tasks", tags=["tasks"])


# CREATE: POST /tasks
@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(**task_in.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# READ ALL: GET /tasks (with filters and pagination)
@router.get("", response_model=list[TaskResponse])
def list_tasks(
    completed: bool | None = None,
    priority: Priority | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(Task.owner_id == current_user.id)
    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority is not None:
        query = query.where(Task.priority == priority)
    query = query.order_by(Task.id).offset(skip).limit(limit)
    return db.scalars(query).all()


# READ ONE: GET /tasks/{task_id}
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_task_or_404(db, task_id, current_user.id)


# UPDATE: PATCH /tasks/{task_id}
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_user_task_or_404(db, task_id, current_user.id)
    for field, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# DELETE: DELETE /tasks/{task_id}
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_user_task_or_404(db, task_id, current_user.id)
    db.delete(task)
    db.commit()


# AI SUGGESTION (placeholder): POST /tasks/{task_id}/suggest
@router.post("/{task_id}/suggest", response_model=TaskSuggestion)
def suggest_for_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_user_task_or_404(db, task_id, current_user.id)

    # Fall back to the title if the task has no description
    description = task.description or task.title

    # Placeholder: a real version would send `description` to an AI service here
    suggestion = (
        f"Suggested next steps for '{task.title}': "
        f"break it into smaller steps, start with the first one today, "
        f"and since it's {task.priority} priority, schedule time for it accordingly."
    )

    return TaskSuggestion(
        task_id=task.id,
        description=description,
        suggestion=suggestion,
    )