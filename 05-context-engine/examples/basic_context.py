from asux_context_engine.context_manager import ContextManager
from asux_context_engine.models import ContextItem, ContextType, SensitivityLevel


def main() -> None:
    print("=== Example A: Basic Context Management ===\n")

    cm = ContextManager()

    # 1. Add Context Items
    item1 = ContextItem(
        content="Customer preferred delivery address: 123 Tech Lane, Dhaka.",
        context_type=ContextType.USER_PROFILE,
        source="profile_service",
        tenant_id="tenant_dhaka",
        priority=7,
        sensitivity=SensitivityLevel.INTERNAL,
    )
    item2 = ContextItem(
        content="Current promotion: 15% discount on all mechanical keyboards with code KEY15.",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        source="marketing_engine",
        tenant_id="tenant_dhaka",
        priority=9,
    )

    id1 = cm.add_item(item1)
    id2 = cm.add_item(item2)
    print(f"Added item 1: {id1}")
    print(f"Added item 2: {id2}")

    # 2. Retrieve by ID
    retrieved = cm.get_item(id1)
    if retrieved:
        print(f"Retrieved item 1 content: '{retrieved.content}'")

    # 3. Update an Item
    item1_updated = retrieved.model_copy(
        update={"content": "Customer preferred address updated: 456 Innovation Ave, Dhaka."}
    )
    cm.update_item(item1_updated)
    print("Updated item 1 content successfully.")

    # 4. List Items
    all_items = cm.list_items(tenant_id="tenant_dhaka")
    print(f"Total items in tenant scope: {len(all_items)}")

    # 5. Delete an Item
    deleted = cm.delete_item(id2)
    print(f"Deleted item 2: {deleted}")
    print(f"Remaining items: {len(cm.list_items(tenant_id='tenant_dhaka'))}")


if __name__ == "__main__":
    main()
