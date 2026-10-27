import pytest

from asux_context_engine.context_manager import ContextManager
from asux_context_engine.exceptions import (
    ContextItemNotFoundError,
    ScopeAccessViolationError,
)
from asux_context_engine.models import ContextItem, ContextQuery, ContextType


def test_manager_crud_operations(context_manager: ContextManager) -> None:
    item = ContextItem(
        content="Customer preference: dark mode.",
        context_type=ContextType.USER_PROFILE,
        tenant_id="tenant-1",
        session_id="session-1",
    )

    # 1. Add
    item_id = context_manager.add_item(item)
    assert item_id == item.id

    # 2. Get
    fetched = context_manager.get_item(item_id)
    assert fetched is not None
    assert fetched.content == item.content

    # 3. Update
    updated = fetched.model_copy(update={"content": "Customer preference: light mode."})
    context_manager.update_item(updated)
    assert context_manager.get_item(item_id).content == "Customer preference: light mode."

    # 4. Delete
    assert context_manager.delete_item(item_id) is True
    assert context_manager.get_item(item_id) is None


def test_manager_update_nonexistent_raises(context_manager: ContextManager) -> None:
    fake_item = ContextItem(id="fake-id", content="Fake", tenant_id="tenant-1")
    with pytest.raises(ContextItemNotFoundError):
        context_manager.update_item(fake_item)


def test_manager_tenant_isolation_in_query(context_manager: ContextManager) -> None:
    # Query without tenant_id must raise ScopeAccessViolationError
    query_no_tenant = ContextQuery(query_text="anything")
    with pytest.raises(ScopeAccessViolationError):
        context_manager.build_context(query_no_tenant)


def test_manager_scoped_retrieval(context_manager: ContextManager) -> None:
    # Add items in two different tenants
    context_manager.add_item(ContextItem(content="Tenant 1 Info", tenant_id="t1"))
    context_manager.add_item(ContextItem(content="Tenant 2 Info", tenant_id="t2"))

    # Query for t1
    q_t1 = ContextQuery(query_text="Info", tenant_id="t1")
    res_t1 = context_manager.build_context(q_t1)

    assert len(res_t1.items) == 1
    assert res_t1.items[0].content == "Tenant 1 Info"


def test_manager_clear_scope(context_manager: ContextManager) -> None:
    context_manager.add_item(ContextItem(content="A1", tenant_id="t1", session_id="s1"))
    context_manager.add_item(ContextItem(content="A2", tenant_id="t1", session_id="s2"))
    context_manager.add_item(ContextItem(content="B1", tenant_id="t2", session_id="s1"))

    # Clear only s1 within t1
    cleared = context_manager.clear_scope(tenant_id="t1", session_id="s1")
    assert cleared == 1
    assert len(context_manager.list_items(tenant_id="t1")) == 1
    assert len(context_manager.list_items(tenant_id="t2")) == 1
