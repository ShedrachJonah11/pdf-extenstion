"""Password validation helpers.

Kept separate from auth.py so the rules can be unit-tested without
loading the JWT or bcrypt machinery.
"""

from __future__ import annotations


COMMON_PASSWORDS = frozenset(
    {
        "password",
        "password1",
        "12345678",
        "qwerty12",
        "qwerty123",
        "iloveyou",
        "letmein1",
        "abc12345",
        "welcome1",
        "trustno1",
    }
)


class PasswordError(ValueError):
    pass


def assert_password_acceptable(password: str) -> None:
    """Raise PasswordError if the password fails minimum complexity rules.

    Required: 8+ characters, at least one letter, at least one digit, and
    not in the common-passwords blacklist.
    """
    if len(password) < 8:
        raise PasswordError("password must be at least 8 characters")
    if password.lower() in COMMON_PASSWORDS:
        raise PasswordError("password is too common")
    if not any(c.isalpha() for c in password):
        raise PasswordError("password must include at least one letter")
    if not any(c.isdigit() for c in password):
        raise PasswordError("password must include at least one digit")
