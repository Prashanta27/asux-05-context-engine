from pydantic import BaseModel, Field, model_validator

from asux_context_engine.exceptions import ContextConfigurationError


class ContextEngineConfig(BaseModel):
    """
    Configuration parameters and global safety boundaries for the Context Engine.
    """

    default_token_budget: int = Field(
        default=2000, gt=0, le=128000, description="Default token budget for context assembly."
    )
    max_items_per_query: int = Field(
        default=50, gt=0, le=500, description="Upper bound on items retrieved per query."
    )
    default_ttl_seconds: int | None = Field(
        default=None,
        gt=0,
        description="Default TTL in seconds for context items without expires_at.",
    )
    max_content_length: int = Field(
        default=10000,
        gt=10,
        le=200000,
        description="Maximum character length of single item content.",
    )
    enforce_tenant_isolation: bool = Field(
        default=True, description="Strictly forbid queries without tenant_id or across tenants."
    )
    chars_per_token_estimate: float = Field(
        default=4.0, gt=1.0, le=10.0, description="Character-to-token ratio for estimation."
    )
    log_level: str = Field(default="INFO", description="Structured logging verbosity.")

    @model_validator(mode="after")
    def validate_budget_and_items(self) -> "ContextEngineConfig":
        if self.default_token_budget < 50:
            raise ContextConfigurationError("default_token_budget cannot be less than 50.")
        return self
