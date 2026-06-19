from app.services.conversation import MAX_TURNS_PER_KEY, ConversationStore, Turn


def test_empty_store_returns_empty_history() -> None:
    store = ConversationStore()
    assert store.get_turns("alice", "doc1") == []


def test_append_and_retrieve_turn() -> None:
    store = ConversationStore()
    turn = Turn(question="hello?", answer="hi")
    store.append_turn("alice", "doc1", turn)
    history = store.get_turns("alice", "doc1")
    assert len(history) == 1
    assert history[0].question == "hello?"


def test_history_is_bounded() -> None:
    store = ConversationStore()
    for i in range(MAX_TURNS_PER_KEY + 5):
        store.append_turn("alice", "doc1", Turn(question=f"q{i}", answer=f"a{i}"))
    history = store.get_turns("alice", "doc1")
    assert len(history) == MAX_TURNS_PER_KEY


def test_clear_drops_history() -> None:
    store = ConversationStore()
    store.append_turn("alice", "doc1", Turn(question="q", answer="a"))
    store.clear("alice", "doc1")
    assert store.get_turns("alice", "doc1") == []


def test_per_user_per_document_isolation() -> None:
    store = ConversationStore()
    store.append_turn("alice", "doc1", Turn("q", "a"))
    assert store.get_turns("bob", "doc1") == []
    assert store.get_turns("alice", "doc2") == []


def test_blank_turn_is_not_appended() -> None:
    store = ConversationStore()
    store.append_turn("alice", "doc1", Turn(question="", answer=""))
    store.append_turn("alice", "doc1", Turn(question="ok", answer="   "))
    assert store.get_turns("alice", "doc1") == []


def test_clear_for_user_drops_only_that_users_conversations() -> None:
    store = ConversationStore()
    store.append_turn("alice", "doc1", Turn("q", "a"))
    store.append_turn("alice", "doc2", Turn("q", "a"))
    store.append_turn("bob", "doc1", Turn("q", "a"))

    cleared = store.clear_for_user("alice")
    assert cleared == 2
    assert store.get_turns("alice", "doc1") == []
    assert store.get_turns("alice", "doc2") == []
    assert len(store.get_turns("bob", "doc1")) == 1
