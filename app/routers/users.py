from fastapi import APIRouter, Depends

from app.models import User
from app.schemas import UserResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
