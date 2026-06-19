from app.services.llm_service import MockBackend, count_tokens


def test_mock_backend_advertises_name() -> None:
    assert MockBackend.name == "mock"


def test_build_prompt_includes_context_and_question() -> None:
    backend = MockBackend()
    prompt = backend.build_prompt(context="paris is the capital of france", question="What is the capital of France?")
    assert "paris is the capital of france" in prompt
    assert "What is the capital of France?" in prompt


def test_count_tokens_returns_positive_integer() -> None:
    assert count_tokens("hello world") > 0


def test_count_tokens_falls_back_for_unknown_model() -> None:
    n = count_tokens("hello world", model="not-a-real-model")
    assert isinstance(n, int)
    assert n > 0


def test_count_tokens_empty_string_is_zero() -> None:
    assert count_tokens("") == 0


def test_history_prompt_lists_previous_turns_in_order() -> None:
    backend = MockBackend()
    prompt = backend.build_prompt_with_history(
        context="ctx",
        question="newq",
        history=[("first", "a1"), ("second", "a2")],
    )
    assert prompt.index("first") < prompt.index("second")
    assert "newq" in prompt
    assert "(none)" not in prompt


def test_history_prompt_shows_none_when_empty() -> None:
    backend = MockBackend()
    prompt = backend.build_prompt_with_history(context="ctx", question="q", history=[])
    assert "(none)" in prompt
