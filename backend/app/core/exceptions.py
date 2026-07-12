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


class ConflictException(AppException):
    """Raised when a request conflicts with current resource state."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class ScannerExecutionException(AppException):
    """Raised when a scanner execution fails."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="SCANNER_EXECUTION_ERROR",
            details=details,
        )


class ScannerTimeoutException(AppException):
    """Raised when a scanner execution exceeds configured timeout."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=504,
            error_code="SCANNER_TIMEOUT",
            details=details,
        )


class ParserException(AppException):
    """Raised when a scan artifact parsing or validation fails."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="PARSER_ERROR",
            details=details,
        )


class UnsupportedProviderException(AppException):
    """Raised when the configured AI provider is not implemented."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="UNSUPPORTED_AI_PROVIDER",
            details=details,
        )


class AIProviderConfigurationException(AppException):
    """Raised when a supported AI provider is missing required configuration."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="AI_PROVIDER_CONFIGURATION_ERROR",
            details=details,
        )


class AIProviderException(AppException):
    """Raised when an AI provider request fails at the transport level
    (network failure, timeout, non-success response, malformed or empty output).
    """
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="AI_PROVIDER_ERROR",
            details=details,
        )


class InvalidAIResponseException(AppException):
    """Raised when an AI provider's output does not satisfy AVAP's
    structured remediation response contract.
    """
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="INVALID_AI_RESPONSE",
            details=details,
        )


class InsufficientContextException(AppException):
    """Raised when the available assessment context is not sufficient to
    generate an AI remediation recommendation.
    """
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="INSUFFICIENT_CONTEXT",
            details=details,
        )
