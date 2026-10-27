from typing import Any

from asux_agent_runtime.models.request import AgentRequest
from asux_agent_runtime.models.response import AgentResponse

from asux_context_engine.context_manager import ContextManager
from asux_context_engine.models import (
    ContextItem,
    ContextQuery,
    ContextResult,
    ContextType,
    SensitivityLevel,
)


class AgentContextAdapter:
    """
    Adapter bridging Project 4 (asux-agent-runtime) and Project 5 (asux-context-engine).
    Allows agents to request relevant context and record execution outcomes.
    """

    def __init__(self, context_manager: ContextManager) -> None:
        self.context_manager = context_manager

    def create_query_from_request(
        self,
        request: AgentRequest,
        limit: int = 10,
        token_budget: int | None = None,
        context_types: list[ContextType] | None = None,
        max_sensitivity: SensitivityLevel | None = None,
    ) -> ContextQuery:
        """
        Constructs a ContextQuery derived from trusted AgentRequest fields.
        """
        return ContextQuery(
            query_text=request.goal,
            session_id=request.conversation_id,
            tenant_id=request.context.tenant_id,
            limit=limit,
            token_budget=token_budget,
            context_types=context_types,
            max_sensitivity=max_sensitivity,
        )

    def retrieve_context_for_request(
        self,
        request: AgentRequest,
        limit: int = 10,
        token_budget: int | None = None,
    ) -> ContextResult:
        """
        Retrieves and formats relevant context for an incoming AgentRequest.
        """
        query = self.create_query_from_request(request, limit=limit, token_budget=token_budget)
        return self.context_manager.build_context(query)

    def attach_context_to_metadata(
        self,
        request: AgentRequest,
        context_result: ContextResult,
    ) -> AgentRequest:
        """
        Attaches formatted context and item metadata to an AgentRequest
        without mutating caller context.
        """
        new_metadata: dict[str, Any] = dict(request.metadata)
        new_metadata["formatted_context"] = context_result.formatted_context
        new_metadata["context_item_ids"] = [item.id for item in context_result.items]
        new_metadata["context_tokens_estimated"] = context_result.total_tokens_estimated

        return request.model_copy(update={"metadata": new_metadata})

    def record_response_outcome(
        self,
        response: AgentResponse,
        tenant_id: str,
        session_id: str | None = None,
    ) -> str | None:
        """
        Records the final response of an agent run into the context engine as session history.
        """
        if not response.final_response:
            return None

        item = ContextItem(
            content=f"Agent response (status: {response.status.value}): {response.final_response}",
            context_type=ContextType.SESSION_HISTORY,
            source="agent:commerce_assistant",
            tenant_id=tenant_id,
            session_id=session_id or response.conversation_id,
            priority=6,
            metadata={
                "run_id": response.run_id,
                "status": response.status.value,
                "steps_executed": response.steps_executed,
            },
        )
        return self.context_manager.add_item(item)
