from asux_agent_runtime.models.request import AgentRequest
from asux_tool_runtime.models.context import PermissionContext

from asux_context_engine.adapters.agent_adapter import AgentContextAdapter
from asux_context_engine.adapters.llm_adapter import LLMContextAdapter
from asux_context_engine.context_manager import ContextManager
from asux_context_engine.models import ContextItem, ContextType


def main() -> None:
    print("=== Example D: Agent Runtime & LLM Gateway Integration ===\n")

    # 1. Initialize Context Manager and Adapter
    cm = ContextManager()
    agent_adapter = AgentContextAdapter(context_manager=cm)

    # 2. Add customer-specific contextual facts
    cm.add_item(
        ContextItem(
            content="Customer vip_999 is a Platinum Member with 10% lifetime discount.",
            context_type=ContextType.USER_PROFILE,
            source="crm_database",
            tenant_id="tenant_prime",
            session_id="session_42",
            priority=9,
        )
    )
    cm.add_item(
        ContextItem(
            content="Customer previously inquired about MacBook Pro M3 stock availability.",
            context_type=ContextType.SESSION_HISTORY,
            source="chat_history",
            tenant_id="tenant_prime",
            session_id="session_42",
            priority=7,
        )
    )

    # 3. Simulate an AgentRequest from Project 4
    perm_context = PermissionContext(
        principal_id="user_platinum",
        principal_type="customer",
        tenant_id="tenant_prime",
        permissions=["product:read", "order:read"],
    )

    agent_req = AgentRequest(
        goal="What discount can I get on MacBook Pro?",
        conversation_id="session_42",
        context=perm_context,
    )

    print(f"Original Agent Goal: '{agent_req.goal}'")

    # 4. Retrieve context via AgentContextAdapter
    context_result = agent_adapter.retrieve_context_for_request(agent_req, token_budget=500)
    print(f"Context items retrieved: {len(context_result.items)}")

    # 5. Attach to AgentRequest metadata
    enriched_req = agent_adapter.attach_context_to_metadata(agent_req, context_result)
    print(
        f"Enriched Metadata keys: {list(enriched_req.metadata.keys())} "
        f"(Tokens: {enriched_req.metadata.get('context_tokens_estimated')})"
    )

    # 6. Adapt to LLM Gateway Message format
    system_message = LLMContextAdapter.to_system_message(context_result)
    print(f"\nGenerated LLM Gateway Message (Role: {system_message.role.value}):")
    print(system_message.content)


if __name__ == "__main__":
    main()
