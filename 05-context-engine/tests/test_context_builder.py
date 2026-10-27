from asux_context_engine.context_builder import ContextBuilder
from asux_context_engine.models import ContextItem, ContextQuery, ContextType


def test_builder_end_to_end_assembly(context_builder: ContextBuilder) -> None:
    item1 = ContextItem(
        content="Product Alpha is in stock and costs $50.",
        tenant_id="t1",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        priority=10,
    )
    item2 = ContextItem(
        content="Product Beta is out of stock.",
        tenant_id="t1",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        priority=5,
    )

    query = ContextQuery(query_text="Product stock", tenant_id="t1", token_budget=500)
    result = context_builder.build(query, [item1, item2])

    assert len(result.items) == 2
    assert result.total_tokens_estimated > 0
    assert result.excluded_count == 0
    assert "=== BEGIN CONTEXT BLOCK (UNTRUSTED DATA) ===" in result.formatted_context
    assert "Product Alpha is in stock" in result.formatted_context


def test_builder_token_budget_pruning(context_builder: ContextBuilder) -> None:
    # Set a tiny token budget of only 25 tokens
    item1 = ContextItem(
        content="First priority item that easily fits in the budget.",
        tenant_id="t1",
        priority=10,
    )
    item2 = ContextItem(
        content="Second priority item that will be excluded due to budget constraints.",
        tenant_id="t1",
        priority=2,
    )

    query = ContextQuery(query_text="item", tenant_id="t1", token_budget=25)
    result = context_builder.build(query, [item1, item2])

    assert len(result.items) == 1
    assert result.items[0].content == item1.content
    assert result.excluded_count == 1
    assert len(result.warnings) == 1
    assert "skipped due to token budget" in result.warnings[0]


def test_builder_empty_candidates(context_builder: ContextBuilder) -> None:
    query = ContextQuery(query_text="anything", tenant_id="t1")
    result = context_builder.build(query, [])

    assert len(result.items) == 0
    assert result.formatted_context == ""
    assert result.total_tokens_estimated == 0
