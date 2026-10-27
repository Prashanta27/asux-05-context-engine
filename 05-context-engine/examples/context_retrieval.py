from datetime import UTC, datetime, timedelta

from asux_context_engine.context_manager import ContextManager
from asux_context_engine.models import ContextItem, ContextQuery, ContextType


def main() -> None:
    print("=== Example B: Retrieval and Ranking ===\n")

    cm = ContextManager()
    now = datetime.now(UTC)

    # 1. Populate store with various items
    cm.add_item(
        ContextItem(
            content="Return policy: 30 days money-back guarantee for unused electronics.",
            context_type=ContextType.FACTUAL_KNOWLEDGE,
            source="kb_store",
            tenant_id="tenant_commerce",
            priority=8,
            created_at=now - timedelta(days=2),
        )
    )
    cm.add_item(
        ContextItem(
            content="Special return policy: Laptops have 14 days inspection return window.",
            context_type=ContextType.FACTUAL_KNOWLEDGE,
            source="kb_store",
            tenant_id="tenant_commerce",
            priority=10,
            created_at=now - timedelta(hours=1),
        )
    )
    cm.add_item(
        ContextItem(
            content="Office location: Head office is situated in Gulshan, Dhaka.",
            context_type=ContextType.FACTUAL_KNOWLEDGE,
            source="kb_store",
            tenant_id="tenant_commerce",
            priority=3,
            created_at=now - timedelta(days=10),
        )
    )

    # 2. Query specifically for return policy on laptops
    query = ContextQuery(
        query_text="laptop return policy window",
        tenant_id="tenant_commerce",
        limit=5,
        token_budget=500,
    )

    result = cm.build_context(query)

    print(f"Retrieved {len(result.items)} relevant items:")
    for i, score_entry in enumerate(result.scores, 1):
        item = score_entry.item
        print(f"\n[{i}] Score: {score_entry.score:.4f} | Breakdown: {score_entry.breakdown}")
        print(f"    Content: {item.content}")

    print("\nFormatted Context String:")
    print(result.formatted_context)


if __name__ == "__main__":
    main()
