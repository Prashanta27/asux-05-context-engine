from datetime import datetime

from asux_context_engine.config import ContextEngineConfig
from asux_context_engine.context_builder import ContextBuilder
from asux_context_engine.context_store import ContextStore, InMemoryContextStore
from asux_context_engine.exceptions import (
    ContextItemNotFoundError,
    PolicyViolationError,
    ScopeAccessViolationError,
)
from asux_context_engine.models import (
    ContextItem,
    ContextQuery,
    ContextResult,
    ContextType,
)
from asux_context_engine.policies import ContextPolicy


class ContextManager:
    """
    Primary user-facing facade for the AsuX Context Engine.
    Coordinates storage, policy enforcement, lifecycle management, and context assembly.
    """

    def __init__(
        self,
        store: ContextStore | None = None,
        policy: ContextPolicy | None = None,
        builder: ContextBuilder | None = None,
        config: ContextEngineConfig | None = None,
    ) -> None:
        self.config = config or ContextEngineConfig()
        self.store = store or InMemoryContextStore()
        self.policy = policy or ContextPolicy(
            max_item_content_chars=self.config.max_content_length,
            enforce_strict_tenant_isolation=self.config.enforce_tenant_isolation,
        )
        self.builder = builder or ContextBuilder(
            policy=self.policy,
            default_token_budget=self.config.default_token_budget,
        )

    def add_item(self, item: ContextItem) -> str:
        """
        Validates and stores a new ContextItem.
        Raises PolicyViolationError or InvalidContextItemError if validation fails.
        """
        self.policy.validate_item(item)
        self.store.add(item)
        return item.id

    def get_item(self, item_id: str) -> ContextItem | None:
        """Retrieves a context item by ID."""
        return self.store.get(item_id)

    def update_item(self, item: ContextItem) -> None:
        """
        Updates an existing context item after policy validation.
        Raises ContextItemNotFoundError if the item does not exist.
        """
        if self.store.get(item.id) is None:
            raise ContextItemNotFoundError(f"ContextItem '{item.id}' does not exist.")
        self.policy.validate_item(item)
        self.store.update(item)

    def delete_item(self, item_id: str) -> bool:
        """Deletes a context item by ID. Returns True if deleted, False otherwise."""
        return self.store.delete(item_id)

    def list_items(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        context_types: list[ContextType] | None = None,
    ) -> list[ContextItem]:
        """Lists context items within the specified scope."""
        return self.store.list(
            tenant_id=tenant_id,
            session_id=session_id,
            task_id=task_id,
            context_types=context_types,
        )

    def clear_scope(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        force_all: bool = False,
    ) -> int:
        """
        Clears items within an explicit tenant or session scope.
        Requires explicit scope or force_all=True.
        """
        return self.store.clear(
            tenant_id=tenant_id,
            session_id=session_id,
            force_all=force_all,
        )

    def expire_stale_items(self, now: datetime | None = None) -> int:
        """Removes expired items from storage."""
        return self.store.expire_stale(now=now)

    def build_context(self, query: ContextQuery) -> ContextResult:
        """
        Retrieves, deduplicates, ranks, and budgets context for an agent query.
        """
        allowed, reason = self.policy.is_query_allowed(query)
        if not allowed:
            if "tenant" in (reason or "").lower():
                raise ScopeAccessViolationError(reason or "Tenant scope validation failed.")
            raise PolicyViolationError(reason or "Query not allowed by active policy.")

        # Query candidates from store within scope
        candidates = self.store.list(
            tenant_id=query.tenant_id,
            session_id=query.session_id,
            task_id=query.task_id,
            context_types=query.context_types,
        )

        return self.builder.build(query=query, raw_candidates=candidates)
