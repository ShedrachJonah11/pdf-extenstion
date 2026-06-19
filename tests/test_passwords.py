import pytest

from app.auth.passwords import PasswordError, assert_password_acceptable


def test_accepts_reasonable_password() -> None:
    assert_password_acceptable("hunter22-ok")


def test_rejects_short_password() -> None:
    with pytest.raises(PasswordError):
        assert_password_acceptable("abc1")


def test_rejects_common_password() -> None:
    with pytest.raises(PasswordError):
        assert_password_acceptable("password")


def test_rejects_no_digit() -> None:
    with pytest.raises(PasswordError):
        assert_password_acceptable("onlyletters")


def test_rejects_no_letter() -> None:
    with pytest.raises(PasswordError):
        assert_password_acceptable("12345678")
