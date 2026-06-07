from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.auth.passwords import PasswordError, assert_password_acceptable
from app.config import settings
from app.exceptions import UsernameAlreadyExistsError

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# In-memory user store (swap for a database in production)
_users: dict[str, str] = {}  # username → hashed_password


def user_count() -> int:
    return len(_users)


def user_exists(username: str) -> bool:
    return username in _users


def register_user(username: str, password: str) -> None:
    if username in _users:
        raise UsernameAlreadyExistsError(f"Username '{username}' already exists")
    try:
        assert_password_acceptable(password)
    except PasswordError as e:
        raise ValueError(str(e)) from e
    _users[username] = pwd_context.hash(password)
    logger.info("Registered user: %s", username)


def authenticate_user(username: str, password: str) -> bool:
    hashed = _users.get(username)
    if hashed is None:
        # Verify against a throwaway hash so the timing of a missing user
        # matches that of a bad password.
        pwd_context.verify(password, pwd_context.hash("not-a-real-secret"))
        return False
    return pwd_context.verify(password, hashed)


def create_access_token(username: str, expires_in_minutes: int | None = None) -> str:
    minutes = expires_in_minutes if expires_in_minutes is not None else settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str | None = payload.get("sub")
        if username is None or username not in _users:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username
