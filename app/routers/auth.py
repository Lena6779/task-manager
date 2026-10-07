"""Authentication endpoints: registration and login."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import DuplicateException, ForbiddenException
from app.models import User
from app.schemas import Token, UserCreate
from app.utils.auth import create_access_token, hash_password, verify_password
from app.utils.background import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new user with a hashed password and return an access token.

    Returns 409 if the email is already registered.
    """
    existing = db.scalar(select(User).where(User.email == user_in.email))
    if existing:
        raise DuplicateException("Email already registered")

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # loads the database-generated id

    background_tasks.add_task(log_activity, user.id, "registered")
    return Token(access_token=create_access_token(user.id))


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Validate credentials and return an access token.

    Expects form data with ``username`` (the user's email) and
    ``password``. Returns 401 for wrong credentials, 403 for inactive accounts.
    """
    # OAuth2 always names this field "username"; here it holds the email
    user = db.scalar(select(User).where(User.email == form_data.username))
    # One combined check and one message, so attackers can't tell
    # whether the email or the password was wrong
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise ForbiddenException("This account is inactive")
    return Token(access_token=create_access_token(user.id))