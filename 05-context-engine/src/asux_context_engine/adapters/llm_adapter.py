from asux_llm_gateway.models.messages import Message, MessageRole

from asux_context_engine.models import ContextResult


class LLMContextAdapter:
    """
    Adapter bridging Project 5 (asux-context-engine) and Project 1 (asux-llm-gateway).
    Translates ContextResults into standardized Gateway Message objects with boundary delimiters.
    """

    @classmethod
    def to_system_message(cls, context_result: ContextResult) -> Message:
        """
        Converts a ContextResult into a system-level Message.
        """
        content = context_result.formatted_context or "No relevant context available."
        return Message.system(content=content)

    @classmethod
    def to_user_message(cls, context_result: ContextResult) -> Message:
        """
        Converts a ContextResult into a user-level contextual Message.
        """
        content = context_result.formatted_context or "No relevant context available."
        return Message.user(content=content)

    @classmethod
    def to_messages(
        cls,
        context_result: ContextResult,
        as_system: bool = True,
    ) -> list[Message]:
        """
        Returns a list of messages containing the delimited context.
        """
        role = MessageRole.SYSTEM if as_system else MessageRole.USER
        content = context_result.formatted_context or "No context retrieved."
        return [Message(role=role, content=content)]
