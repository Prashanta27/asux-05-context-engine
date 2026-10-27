from datetime import timedelta

import pytest

from asux_context_engine.context_store import InMemoryContextStore
from asux_context_engine.exceptions import (
    ContextItemNotFoundError,
    ScopeAccessViolationError,
)
from asux_context_engine.models import ContextItem, ContextType, utc_now


def test_store_add_get_delete(
    in_memory_store: InMemoryContextStore, sample_item: ContextItem
) -> None:
    in_memory_store.add(sample_item)
    fetched = in_memory_store.get(sample_item.id)
    assert fetched is not None
    assert fetched.id == sample_item.id
    assert fetched.content == sample_item.content

    # Delete
    assert in_memory_store.delete(sample_item.id) is True
    assert in_memory_store.get(sample_item.id) is None
    assert in_memory_store.delete(sample_item.id) is False


def test_store_update(in_memory_store: InMemoryContextStore, sample_item: ContextItem) -> None:
    in_memory_store.add(sample_item)
    updated = sample_item.model_copy(update={"content": "Updated content string."})
    in_memory_store.update(updated)

    fetched = in_memory_store.get(sample_item.id)
    assert fetched is not None
    assert fetched.content == "Updated content string."

    # Update non-existent
    ghost_item = ContextItem(id="ghost", content="Ghost", tenant_id="tenant-1")
    with pytest.raises(ContextItemNotFoundError):
        in_memory_store.update(ghost_item)


def test_store_list_filtering(in_memory_store: InMemoryContextStore) -> None:
    item_t1_s1 = ContextItem(
        content="T1 S1",
        tenant_id="tenant-1",
        session_id="session-1",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
    )
    item_t1_s2 = ContextItem(
        content="T1 S2",
        tenant_id="tenant-1",
        session_id="session-2",
        context_type=ContextType.USER_PROFILE,
    )
    item_t2_s1 = ContextItem(
        content="T2 S1",
        tenant_id="tenant-2",
        session_id="session-1",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
    )

    in_memory_store.add(item_t1_s1)
    in_memory_store.add(item_t1_s2)
    in_memory_store.add(item_t2_s1)

    # Filter by tenant
    t1_items = in_memory_store.list(tenant_id="tenant-1")
    assert len(t1_items) == 2

    # Filter by session
    s1_items = in_memory_store.list(session_id="session-1")
    assert len(s1_items) == 2

    # Filter by tenant + session
    t1_s1_items = in_memory_store.list(tenant_id="tenant-1", session_id="session-1")
    assert len(t1_s1_items) == 1
    assert t1_s1_items[0].content == "T1 S1"

    # Filter by type
    profiles = in_memory_store.list(context_types=[ContextType.USER_PROFILE])
    assert len(profiles) == 1
    assert profiles[0].content == "T1 S2"


def test_store_safe_clear(in_memory_store: InMemoryContextStore) -> None:
    item1 = ContextItem(content="C1", tenant_id="t1", session_id="s1")
    item2 = ContextItem(content="C2", tenant_id="t2", session_id="s1")
    in_memory_store.add(item1)
    in_memory_store.add(item2)

    # Clearing without scope must raise ScopeAccessViolationError
    with pytest.raises(ScopeAccessViolationError):
        in_memory_store.clear()

    # Clear scoped to t1
    deleted_count = in_memory_store.clear(tenant_id="t1")
    assert deleted_count == 1
    assert in_memory_store.get(item1.id) is None
    assert in_memory_store.get(item2.id) is not None

    # Global clear with force_all
    assert in_memory_store.clear(force_all=True) == 1
    assert len(in_memory_store.list()) == 0


def test_store_expire_stale(in_memory_store: InMemoryContextStore) -> None:
    now = utc_now()
    active_item = ContextItem(
        content="Active",
        tenant_id="t1",
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )
    stale_item = ContextItem(
        content="Stale",
        tenant_id="t1",
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1),
    )
    permanent_item = ContextItem(content="Permanent", tenant_id="t1", created_at=now)

    in_memory_store.add(active_item)
    in_memory_store.add(stale_item)
    in_memory_store.add(permanent_item)

    purged = in_memory_store.expire_stale(now=now)
    assert purged == 1
    assert in_memory_store.get(stale_item.id) is None
    assert in_memory_store.get(active_item.id) is not None
    assert in_memory_store.get(permanent_item.id) is not None
