from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetails(BaseModel):
    """Standardized error details model."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel, Generic[T]):
    """Standardized success response envelope."""

    success: bool = True
    data: T
    error: None = None


class ErrorResponse(BaseModel):
    """Standardized error response envelope."""

    success: bool = False
    data: None = None
    error: ErrorDetails
