from typing import Any


class AppException(Exception):
    """Base exception for all application-specific errors.
    
    Ensures consistent error handling across the platform without exposing
    internal implementation details to the client.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationException(AppException):
    """Raised when business validation rules fail."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class DuplicateException(AppException):
    """Raised when a resource already exists and duplicates are not allowed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class InternalException(AppException):
    """Raised for unexpected internal errors that should be sanitized for the client."""
    def __init__(self, message: str = "An unexpected error occurred."):
        super().__init__(
            message=message,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
        )
