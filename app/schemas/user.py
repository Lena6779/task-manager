"""Pydantic schemas for users and authentication tokens."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for creating/registering new user."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    # Bycrpt ONLY uses the first 72 bytes of a password
    password: str = Field(..., min_length=8, max_length=72)


class UserResponse(BaseModel):
    """Public user profile.
    Intentionally has NO password field, so the hash can NEVER be returned to a client for security reasons.
    """
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    is_active:  bool
    created_at: datetime 

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example":{
                "id": 1,
                "name": "Dyson Thorne",
                "email": "dyson.thorne@example.com",
                "is_active": bool,
                "created_at": "2023-01-01T00:00:00"
            }
        }

        )


class Token(BaseModel):
    """JWT access token returned after register or login."""
    access_token: str = Field(..., min_length=1)
    token_type: str = Field("bearer", pattern="^bearer$")
