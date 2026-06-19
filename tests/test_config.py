import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_defaults_load() -> None:
    s = Settings()
    assert s.access_token_expire_minutes > 0
    assert s.max_upload_size_mb > 0
    assert s.llm_request_timeout > 0


def test_settings_rejects_zero_token_ttl() -> None:
    with pytest.raises(ValidationError):
        Settings(access_token_expire_minutes=0)


def test_settings_rejects_negative_upload_cap() -> None:
    with pytest.raises(ValidationError):
        Settings(max_upload_size_mb=-1)


def test_cors_origins_list_splits_csv() -> None:
    s = Settings(cors_allow_origins="https://a.com, https://b.com")
    assert s.cors_origins_list == ["https://a.com", "https://b.com"]


def test_cors_origins_list_returns_wildcard_for_star() -> None:
    s = Settings(cors_allow_origins="*")
    assert s.cors_origins_list == ["*"]
