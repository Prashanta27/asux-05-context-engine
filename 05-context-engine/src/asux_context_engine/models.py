import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ContextType(StrEnum):
    """
    Standard categorization for contextual information items.
    """

    SYSTEM_INSTRUCTION = "system_instruction"
    USER_PROFILE = "user_profile"
    SESSION_HISTORY = "session_history"
    FACTUAL_KNOWLEDGE = "factual_knowledge"
    TOOL_OUTPUT = "tool_output"
    TASK_STATE = "task_state"
    EXTERNAL_DOCUMENT = "external_document"
    CUSTOM = "custom"


class SensitivityLevel(StrEnum):
    """
    Security sensitivity classification for context items.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

    @property
    def rank(self) -> int:
        ranks = {
            SensitivityLevel.PUBLIC: 1,
            SensitivityLevel.INTERNAL: 2,
            SensitivityLevel.CONFIDENTIAL: 3,
            SensitivityLevel.RESTRICTED: 4,
        }
        return ranks[self]


def utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(UTC)


class ContextItem(BaseModel):
    """
    Validated representation of a discrete piece of contextual information.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, description="Unique item ID.")
    content: str = Field(..., min_length=1, description="The textual content.")
    context_type: ContextType = Field(
        default=ContextType.FACTUAL_KNOWLEDGE, description="Categorization type."
    )
    source: str = Field(default="system", description="Origin of this context item.")
    created_at: datetime = Field(
        default_factory=utc_now, description="Timezone-aware creation timestamp."
    )
    expires_at: datetime | None = Field(default=None, description="Optional expiration timestamp.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Structured metadata attributes."
    )
    priority: int = Field(
        default=5, ge=0, le=100, description="Priority score from 0 (lowest) to 100 (highest)."
    )

    # Scoping attributes
    session_id: str | None = Field(default=None, description="Bound session identifier.")
    task_id: str | None = Field(default=None, description="Bound task identifier.")
    tenant_id: str | None = Field(default=None, description="Bound tenant identifier.")

    # Sensitivity
    sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.INTERNAL, description="Security sensitivity classification."
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("ContextItem content cannot be empty or whitespace only.")
        return stripped

    @field_validator("created_at")
    @classmethod
    def ensure_created_at_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v

    @field_validator("expires_at")
    @classmethod
    def ensure_expires_at_tz_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v

    @model_validator(mode="after")
    def validate_expiration_after_creation(self) -> "ContextItem":
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be strictly after created_at.")
        return self

    def is_expired(self, now: datetime | None = None) -> bool:
        """Checks if the context item has passed its expiration deadline."""
        if self.expires_at is None:
            return False
        current_time = now if now is not None else utc_now()
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=UTC)
        return current_time >= self.expires_at


class ContextQuery(BaseModel):
    """
    Validated request specification for context retrieval.
    """

    query_text: str = Field(default="", description="Search query or task description.")
    session_id: str | None = Field(default=None, description="Filter by session ID.")
    task_id: str | None = Field(default=None, description="Filter by task ID.")
    tenant_id: str | None = Field(default=None, description="Filter by tenant ID.")
    limit: int = Field(default=10, gt=0, le=100, description="Maximum number of items to return.")
    context_types: list[ContextType] | None = Field(
        default=None, description="Filter by specific context types."
    )
    metadata_filter: dict[str, Any] | None = Field(
        default=None, description="Key-value filters that must match item metadata."
    )
    max_sensitivity: SensitivityLevel | None = Field(
        default=None, description="Highest sensitivity allowed in retrieved results."
    )
    token_budget: int | None = Field(
        default=None, gt=0, description="Target token budget constraint."
    )


class ContextScore(BaseModel):
    """
    Detailed scoring information for a ranked context item.
    """

    item: ContextItem = Field(..., description="The context item being evaluated.")
    score: float = Field(..., ge=0.0, description="Overall relevance/importance score.")
    breakdown: dict[str, float] = Field(
        default_factory=dict, description="Component score breakdown (text, priority, recency)."
    )


class ContextResult(BaseModel):
    """
    Structured response containing assembled context items and execution metadata.
    """

    items: list[ContextItem] = Field(
        default_factory=list, description="Selected and ordered context items."
    )
    scores: list[ContextScore] = Field(
        default_factory=list, description="Score entries corresponding to items."
    )
    total_tokens_estimated: int = Field(
        default=0, ge=0, description="Total estimated tokens across all selected items."
    )
    budget_limit: int | None = Field(
        default=None, description="Token budget limit applied during assembly."
    )
    excluded_count: int = Field(
        default=0, ge=0, description="Number of candidate items excluded due to budget or policy."
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal warnings encountered during assembly."
    )
    formatted_context: str = Field(
        default="", description="Delimited text representation formatted for model consumption."
    )
    retrieval_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata regarding ranking and filtering."
    )
