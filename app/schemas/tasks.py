"""Pydantic schemas for task requests and responses."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.tasks import Priority


class TaskBase(BaseModel):
    """Fields shared by task creation and task response."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    priority: Priority = "medium"


class TaskCreate(TaskBase):
    """Request body for creating a task.
    ''user_id'' is deliberately absent: the server sets it from the authenticated user so clients CAN'T create tasks for others!"""
    pass


class TaskUpdate(BaseModel):
    """Request body for a partial update. Every field is optional."""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None


class TaskResponse(TaskBase):
    """Task data returned by the API."""
    id: int = Field(..., ge=1)
    completed: bool
    user_id: int= Field(..., ge=1)
    created_at: datetime
    updated_at: datetime 
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Example Task",
                "description": "This is an example task.",
                "priority": "medium",
                "completed": False,
                "user_id": 1,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )                  

class SuggestRequest(BaseModel):
    """Optional body for the suggest endpoint.
    If no descriptionm is sent, the task's saved description is used.""" 
    description: str | None =Field(None, min_length=1, max_length=2000)                           

class TaskSuggestion(BaseModel):
    """Response from the sugesstion endpoint."""
    task_id: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=2000)
    suggestion: str = Field(..., min_length=1)
    # Flags that the suggestion is canned text, not REAL AI output! 
    is_placeholder: bool = True

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "task_id": 1,
                "description": "Example task description.",
                "suggestion": "Example suggestion.",
                "is_placeholder": True
            }
        }
    )

