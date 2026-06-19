import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, UserCreate


def test_user_create_accepts_simple_credentials() -> None:
    u = UserCreate(username="alice", password="hunter22")
    assert u.username == "alice"


def test_user_create_rejects_short_username() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="ab", password="hunter22")


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="alice", password="abc")


def test_user_create_rejects_funky_chars() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="alice!", password="hunter22")


def test_user_create_allows_dot_dash_underscore() -> None:
    UserCreate(username="alice.b-1_x", password="hunter22")


def test_chat_request_defaults_top_k_to_five() -> None:
    req = ChatRequest(document_id="abc", question="hello?")
    assert req.top_k == 5


def test_chat_request_strips_whitespace_question() -> None:
    req = ChatRequest(document_id="abc", question="   hi   ")
    assert req.question == "hi"


def test_chat_request_rejects_blank_question() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(document_id="abc", question="    ")


def test_chat_request_caps_top_k() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(document_id="abc", question="hi", top_k=999)
