from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Priority = Literal["low", "medium", "high"]


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    priority: Priority = "medium"


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None


class TaskResponse(TaskBase):
    id: int
    completed: bool
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSuggestion(BaseModel):
    task_id: int
    description: str
    suggestion: str
    is_placeholder: bool = True