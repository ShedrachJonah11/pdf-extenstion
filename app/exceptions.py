"""Typed application exceptions.

Each exception carries an error_code that maps to a stable string for
clients. Using typed exceptions keeps route handlers focused on HTTP and
the service layer focused on domain logic.
"""

from __future__ import annotations


class AppError(Exception):
    """Base for all expected application errors."""

    error_code: str = "app_error"
    status_code: int = 500

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(error_code={self.error_code!r}, status_code={self.status_code})"


class DocumentNotFoundError(AppError):
    error_code = "document_not_found"
    status_code = 404


class DocumentProcessingError(AppError):
    error_code = "document_processing_error"
    status_code = 422


class EmptyPdfError(DocumentProcessingError):
    error_code = "empty_pdf"


class InvalidPdfError(DocumentProcessingError):
    error_code = "invalid_pdf"


class UploadTooLargeError(AppError):
    error_code = "upload_too_large"
    status_code = 413


class UsernameAlreadyExistsError(AppError):
    error_code = "username_exists"
    status_code = 409


class InvalidCredentialsError(AppError):
    error_code = "invalid_credentials"
    status_code = 401


class ForbiddenError(AppError):
    error_code = "forbidden"
    status_code = 403


class RateLimitedError(AppError):
    error_code = "rate_limited"
    status_code = 429
