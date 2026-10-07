"""Custom exceptions and global handlers that return one consistent JSON error format:
{"error": "Not found", "message":"Task 5 not found", "status_code": 404}"""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base class for the app's own errors."""

    status_code = 500
    error = "InternalError"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    status_code = 404
    error = "NotFound"


class DuplicateException(AppException):
    """Raised when creating something that must be unique already exists."""

    status_code = 409
    error = "Duplicate"


class ForbiddenException(AppException):
    """Raised when a user tries to access something they don't own."""

    status_code = 403
    error = "Forbidden"


def error_response(
    status_code: int,
    error: str,
    message: str,
    details=None,
    headers: dict | None = None,
) -> JSONResponse:
    """Build an error response in the app's standard format."""
    content = {"error": error, "message": message, "status_code": status_code}
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content, headers=headers)


async def app_exception_handler(request: Request, exc: AppException):
    """Handle NotFound, Duplicate, and Forbidden exceptions."""
    return error_response(exc.status_code, exc.error, exc.message)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle FastAPI's built-in HTTP errors, such as 401 Unauthorized."""
    # Keep headers like WWW-Authenticate that auth errors rely on
    return error_response(
        exc.status_code, "HTTPError", str(exc.detail), headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation failures (422)."""
    return error_response(
        422,
        "ValidationError",
        "Request validation failed",
        details=jsonable_encoder(exc.errors()),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)