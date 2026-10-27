from asux_context_engine.deduplication import ContextDeduplicator
from asux_context_engine.models import ContextItem, ContextType


def test_deduplicator_exact_match(deduplicator: ContextDeduplicator) -> None:
    item1 = ContextItem(
        content="Customer is eligible for free shipping.",
        tenant_id="t1",
        priority=3,
        metadata={"source_system": "crm"},
    )
    item2 = ContextItem(
        content="Customer is eligible for free shipping.",
        tenant_id="t1",
        priority=8,
        metadata={"verified": True},
    )

    deduped = deduplicator.deduplicate([item1, item2])
    assert len(deduped) == 1
    # Priority must be the maximum of the two
    assert deduped[0].priority == 8
    # Metadata must be merged
    assert deduped[0].metadata["source_system"] == "crm"
    assert deduped[0].metadata["verified"] is True


def test_deduplicator_normalized_whitespace_and_case(deduplicator: ContextDeduplicator) -> None:
    item1 = ContextItem(
        content="Order #1001   has shipped.",
        tenant_id="t1",
        priority=5,
    )
    item2 = ContextItem(
        content="order #1001 has shipped.",
        tenant_id="t1",
        priority=7,
    )

    deduped = deduplicator.deduplicate([item1, item2], use_normalized=True)
    assert len(deduped) == 1
    assert deduped[0].priority == 7


def test_deduplicator_distinct_types_not_merged(deduplicator: ContextDeduplicator) -> None:
    # Same content but different ContextType must NOT be merged
    item1 = ContextItem(
        content="Always verify user ID.",
        context_type=ContextType.SYSTEM_INSTRUCTION,
        tenant_id="t1",
    )
    item2 = ContextItem(
        content="Always verify user ID.",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        tenant_id="t1",
    )

    deduped = deduplicator.deduplicate([item1, item2])
    assert len(deduped) == 2


def test_deduplicator_unicode_nfkc(deduplicator: ContextDeduplicator) -> None:
    # Unicode normalized comparison (e.g. ligature vs separate letters)
    item1 = ContextItem(content="café menu", tenant_id="t1")
    item2 = ContextItem(content="cafe\u0301 menu", tenant_id="t1")

    deduped = deduplicator.deduplicate([item1, item2], use_normalized=True)
    assert len(deduped) == 1
