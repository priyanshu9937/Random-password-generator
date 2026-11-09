"""In-memory session history for generated passwords."""

from dataclasses import dataclass
from datetime import datetime

from app.config import MAX_HISTORY_ITEMS


@dataclass(frozen=True)
class HistoryEntry:
    password: str
    generated_at: datetime


class PasswordHistory:
    """Keep only the most recent passwords in application memory."""

    def __init__(self, max_items: int = MAX_HISTORY_ITEMS) -> None:
        if isinstance(max_items, bool) or not isinstance(max_items, int) or max_items < 1:
            raise ValueError("History capacity must be a positive whole number.")
        self._max_items = max_items
        self._entries: list[HistoryEntry] = []

    @property
    def entries(self) -> tuple[HistoryEntry, ...]:
        """Return a read-only snapshot, newest first."""
        return tuple(self._entries)

    def add(self, password: str, generated_at: datetime | None = None) -> HistoryEntry:
        if not isinstance(password, str) or not password:
            raise ValueError("A non-empty password is required for history.")
        entry = HistoryEntry(password, generated_at or datetime.now())
        self._entries.insert(0, entry)
        del self._entries[self._max_items :]
        return entry

    def clear(self) -> None:
        self._entries.clear()
