from app.services.llm_service import MAX_PROMPT_CHARS, MockBackend


def test_build_prompt_caps_long_inputs() -> None:
    backend = MockBackend()
    huge_ctx = "x" * (MAX_PROMPT_CHARS * 2)
    prompt = backend.build_prompt(context=huge_ctx, question="hi?")
    assert len(prompt) <= MAX_PROMPT_CHARS


def test_build_prompt_with_history_caps_long_inputs() -> None:
    backend = MockBackend()
    huge_ctx = "x" * (MAX_PROMPT_CHARS * 2)
    prompt = backend.build_prompt_with_history(
        context=huge_ctx, question="hi?", history=[("q", "a")]
    )
    assert len(prompt) <= MAX_PROMPT_CHARS
