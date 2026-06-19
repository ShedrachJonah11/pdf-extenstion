import pytest

from app.auth import auth
from app.exceptions import UsernameAlreadyExistsError


@pytest.fixture(autouse=True)
def _clear_users():
    auth._users.clear()
    yield
    auth._users.clear()


def test_register_and_authenticate_user() -> None:
    auth.register_user("alice", "hunter22")
    assert auth.authenticate_user("alice", "hunter22") is True
    assert auth.authenticate_user("alice", "wrong") is False


def test_register_rejects_duplicate_username() -> None:
    auth.register_user("alice", "hunter22")
    with pytest.raises(UsernameAlreadyExistsError):
        auth.register_user("alice", "another-password")


def test_authenticate_unknown_user_returns_false() -> None:
    assert auth.authenticate_user("ghost", "anything") is False


def test_access_token_is_decodable() -> None:
    auth.register_user("alice", "hunter22")
    token = auth.create_access_token("alice")
    from jose import jwt

    from app.config import settings
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "alice"
    assert "iat" in payload


def test_access_token_honors_per_call_ttl_override() -> None:
    auth.register_user("alice", "hunter22")
    token = auth.create_access_token("alice", expires_in_minutes=1)
    from jose import jwt

    from app.config import settings
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["exp"] - payload["iat"] <= 60 + 1
