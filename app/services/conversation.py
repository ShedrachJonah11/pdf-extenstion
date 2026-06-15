"""In-process conversation memory.

Keeps a bounded ring of (question, answer) turns per (user, document).
The store is intentionally in-memory and resets on restart — it is enough
for short follow-up questions during a single session.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock

MAX_TURNS_PER_KEY = 8
MAX_KEY_PARTS_LENGTH = 256
MAX_TURN_TEXT_CHARS = 4_000


@dataclass
class Turn:
    question: str
    answer: str

    def is_blank(self) -> bool:
        return not self.question.strip() or not self.answer.strip()


@dataclass
class _Conversation:
    turns: deque[Turn] = field(default_factory=lambda: deque(maxlen=MAX_TURNS_PER_KEY))


class ConversationStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._by_key: dict[tuple[str, str], _Conversation] = {}

    @staticmethod
    def _key(user: str, document_id: str) -> tuple[str, str]:
        if not user or not document_id:
            raise ValueError("user and document_id must both be non-empty")
        if len(user) > MAX_KEY_PARTS_LENGTH or len(document_id) > MAX_KEY_PARTS_LENGTH:
            raise ValueError("conversation key parts exceed allowed length")
        return (user, document_id)

    def get_turns(self, user: str, document_id: str) -> list[Turn]:
        with self._lock:
            conv = self._by_key.get(self._key(user, document_id))
            return list(conv.turns) if conv else []

    def get_turn_count(self, user: str, document_id: str) -> int:
        with self._lock:
            conv = self._by_key.get(self._key(user, document_id))
            return len(conv.turns) if conv else 0

    def append_turn(self, user: str, document_id: str, turn: Turn) -> None:
        if turn.is_blank():
            return
        capped = Turn(
            question=turn.question[:MAX_TURN_TEXT_CHARS],
            answer=turn.answer[:MAX_TURN_TEXT_CHARS],
        )
        with self._lock:
            key = self._key(user, document_id)
            conv = self._by_key.setdefault(key, _Conversation())
            conv.turns.append(capped)

    def clear(self, user: str, document_id: str) -> None:
        with self._lock:
            self._by_key.pop(self._key(user, document_id), None)

    def clear_for_user(self, user: str) -> int:
        """Drop all conversations for *user*. Returns the number cleared."""
        with self._lock:
            keys = [k for k in self._by_key if k[0] == user]
            for k in keys:
                del self._by_key[k]
            return len(keys)


conversation_store = ConversationStore()
