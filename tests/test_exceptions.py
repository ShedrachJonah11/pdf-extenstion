from app.exceptions import (
    AppError,
    DocumentNotFoundError,
    DocumentProcessingError,
    EmptyPdfError,
    InvalidCredentialsError,
    UploadTooLargeError,
    UsernameAlreadyExistsError,
)


def test_all_errors_inherit_app_error() -> None:
    for exc_cls in (
        DocumentNotFoundError,
        DocumentProcessingError,
        EmptyPdfError,
        InvalidCredentialsError,
        UploadTooLargeError,
        UsernameAlreadyExistsError,
    ):
        assert issubclass(exc_cls, AppError)


def test_status_codes_are_appropriate() -> None:
    assert DocumentNotFoundError().status_code == 404
    assert UploadTooLargeError().status_code == 413
    assert UsernameAlreadyExistsError().status_code == 409
    assert InvalidCredentialsError().status_code == 401


def test_empty_pdf_is_a_processing_error() -> None:
    assert issubclass(EmptyPdfError, DocumentProcessingError)
    assert EmptyPdfError().status_code == 422


def test_error_message_round_trip() -> None:
    err = DocumentNotFoundError("doc abc not found")
    assert err.message == "doc abc not found"
    assert err.error_code == "document_not_found"


def test_app_error_repr_includes_code_and_status() -> None:
    r = repr(DocumentNotFoundError("oops"))
    assert "document_not_found" in r
    assert "404" in r
