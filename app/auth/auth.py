from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# In-memory user store (swap for a database in production)
_users: dict[str, str] = {}  # username → hashed_password


def register_user(username: str, password: str) -> None:
    if username in _users:
        raise ValueError("Username already exists")
    _users[username] = pwd_context.hash(password)
    logger.info("Registered user: %s", username)


def authenticate_user(username: str, password: str) -> bool:
    hashed = _users.get(username)
    if hashed is None:
        return False
    return pwd_context.verify(password, hashed)


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
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
