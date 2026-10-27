from datetime import UTC, datetime

import pytest

from asux_context_engine.config import ContextEngineConfig
from asux_context_engine.context_builder import ContextBuilder
from asux_context_engine.context_manager import ContextManager
from asux_context_engine.context_ranker import ContextRanker
from asux_context_engine.context_store import InMemoryContextStore
from asux_context_engine.deduplication import ContextDeduplicator
from asux_context_engine.models import ContextItem, ContextType, SensitivityLevel
from asux_context_engine.policies import ContextPolicy
from asux_context_engine.token_budget import HeuristicTokenCounter, TokenBudgetManager


@pytest.fixture
def now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def sample_item(now: datetime) -> ContextItem:
    return ContextItem(
        id="item-1",
        content="Customer has 500 reward points.",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        source="crm",
        tenant_id="tenant-1",
        session_id="session-1",
        priority=5,
        created_at=now,
        sensitivity=SensitivityLevel.INTERNAL,
    )


@pytest.fixture
def in_memory_store() -> InMemoryContextStore:
    return InMemoryContextStore()


@pytest.fixture
def token_counter() -> HeuristicTokenCounter:
    return HeuristicTokenCounter(chars_per_token=4.0)


@pytest.fixture
def token_budget_manager(token_counter: HeuristicTokenCounter) -> TokenBudgetManager:
    return TokenBudgetManager(max_budget=500, counter=token_counter)


@pytest.fixture
def default_policy() -> ContextPolicy:
    return ContextPolicy(
        enforce_strict_tenant_isolation=True,
        max_item_content_chars=1000,
        max_allowed_sensitivity=SensitivityLevel.RESTRICTED,
    )


@pytest.fixture
def ranker() -> ContextRanker:
    return ContextRanker()


@pytest.fixture
def deduplicator() -> ContextDeduplicator:
    return ContextDeduplicator()


@pytest.fixture
def context_builder(
    default_policy: ContextPolicy,
    ranker: ContextRanker,
    deduplicator: ContextDeduplicator,
) -> ContextBuilder:
    return ContextBuilder(
        policy=default_policy,
        ranker=ranker,
        deduplicator=deduplicator,
        default_token_budget=1000,
    )


@pytest.fixture
def context_manager(
    in_memory_store: InMemoryContextStore,
    default_policy: ContextPolicy,
    context_builder: ContextBuilder,
) -> ContextManager:
    return ContextManager(
        store=in_memory_store,
        policy=default_policy,
        builder=context_builder,
        config=ContextEngineConfig(default_token_budget=1000),
    )
