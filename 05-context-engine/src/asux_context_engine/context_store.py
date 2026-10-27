import threading
from datetime import datetime
from typing import Protocol

from asux_context_engine.exceptions import (
    ContextItemNotFoundError,
    ScopeAccessViolationError,
)
from asux_context_engine.models import ContextItem, ContextType, utc_now


class ContextStore(Protocol):
    """
    Storage abstraction protocol for saving, retrieving, and pruning ContextItems.
    """

    def add(self, item: ContextItem) -> None:
        """Stores a new ContextItem."""
        ...

    def get(self, item_id: str) -> ContextItem | None:
        """Retrieves a ContextItem by its unique identifier, or returns None if not found."""
        ...

    def update(self, item: ContextItem) -> None:
        """Updates an existing ContextItem. Raises ContextItemNotFoundError if missing."""
        ...

    def delete(self, item_id: str) -> bool:
        """Deletes a ContextItem by ID. Returns True if deleted, False if item did not exist."""
        ...

    def list(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        context_types: list[ContextType] | None = None,
    ) -> list[ContextItem]:
        """Lists items satisfying the provided scope and type filters."""
        ...

    def clear(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        force_all: bool = False,
    ) -> int:
        """
        Clears items within an explicit tenant or session scope.
        Requires explicit scope or force_all=True to prevent accidental global wipes.
        """
        ...

    def expire_stale(self, now: datetime | None = None) -> int:
        """Removes expired items and returns the number of items purged."""
        ...


class InMemoryContextStore:
    """
    Thread-safe in-memory ContextStore implementation for local execution and testing.
    """

    def __init__(self) -> None:
        self._items: dict[str, ContextItem] = {}
        self._lock = threading.RLock()

    def add(self, item: ContextItem) -> None:
        with self._lock:
            # Clone model to prevent accidental external mutation
            self._items[item.id] = item.model_copy(deep=True)

    def get(self, item_id: str) -> ContextItem | None:
        with self._lock:
            item = self._items.get(item_id)
            return item.model_copy(deep=True) if item is not None else None

    def update(self, item: ContextItem) -> None:
        with self._lock:
            if item.id not in self._items:
                raise ContextItemNotFoundError(f"ContextItem with ID '{item.id}' does not exist.")
            self._items[item.id] = item.model_copy(deep=True)

    def delete(self, item_id: str) -> bool:
        with self._lock:
            if item_id in self._items:
                del self._items[item_id]
                return True
            return False

    def list(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        context_types: list[ContextType] | None = None,
    ) -> list[ContextItem]:
        with self._lock:
            results: list[ContextItem] = []
            for item in self._items.values():
                if tenant_id is not None and item.tenant_id != tenant_id:
                    continue
                if session_id is not None and item.session_id != session_id:
                    continue
                if task_id is not None and item.task_id != task_id:
                    continue
                if context_types is not None and item.context_type not in context_types:
                    continue
                results.append(item.model_copy(deep=True))
            return results

    def clear(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        force_all: bool = False,
    ) -> int:
        with self._lock:
            if not force_all and tenant_id is None and session_id is None:
                raise ScopeAccessViolationError(
                    "Safety check: Clearing context requires an explicit tenant_id, "
                    "session_id, or force_all=True."
                )

            to_delete: list[str] = []
            for item_id, item in self._items.items():
                if force_all:
                    to_delete.append(item_id)
                    continue

                tenant_matches = tenant_id is None or item.tenant_id == tenant_id
                session_matches = session_id is None or item.session_id == session_id

                if tenant_matches and session_matches:
                    to_delete.append(item_id)

            for item_id in to_delete:
                del self._items[item_id]

            return len(to_delete)

    def expire_stale(self, now: datetime | None = None) -> int:
        with self._lock:
            current_time = now if now is not None else utc_now()
            expired_ids = [
                item_id for item_id, item in self._items.items() if item.is_expired(current_time)
            ]
            for item_id in expired_ids:
                del self._items[item_id]
            return len(expired_ids)
