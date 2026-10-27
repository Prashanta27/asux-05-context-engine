from datetime import timedelta
from typing import Any

from pydantic import BaseModel, Field

from asux_context_engine.exceptions import PolicyViolationError
from asux_context_engine.models import (
    ContextItem,
    ContextQuery,
    ContextType,
    SensitivityLevel,
    utc_now,
)


class ContextPolicy(BaseModel):
    """
    Explicit, configurable policy governing context ingestion, retention, and access.
    """

    allowed_types: list[ContextType] = Field(
        default_factory=lambda: list(ContextType),
        description="Allowed context categories. Items outside this set are rejected.",
    )
    max_item_content_chars: int = Field(
        default=10000,
        gt=10,
        description="Maximum allowed character length for a single item's content.",
    )
    max_context_age: timedelta | None = Field(
        default=None,
        description="Optional maximum age limit. Older items are treated as stale.",
    )
    max_allowed_sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.RESTRICTED,
        description="Upper ceiling on sensitivity level allowed to be stored or retrieved.",
    )
    enforce_strict_tenant_isolation: bool = Field(
        default=True,
        description="Requires tenant_id on all items and queries.",
    )
    forbidden_metadata_keys: list[str] = Field(
        default_factory=lambda: ["api_key", "password", "secret", "private_key", "token"],
        description="Metadata keys that are strictly prohibited to prevent credential leakage.",
    )

    def validate_item(self, item: ContextItem) -> None:
        """
        Validates an incoming ContextItem against policy boundaries.
        Raises PolicyViolationError if an invariant is breached.
        """
        # 1. Type validation
        if item.context_type not in self.allowed_types:
            raise PolicyViolationError(
                f"ContextType '{item.context_type.value}' is not allowed by active policy."
            )

        # 2. Content size limit
        if len(item.content) > self.max_item_content_chars:
            raise PolicyViolationError(
                f"Item content length ({len(item.content)}) exceeds policy maximum of "
                f"{self.max_item_content_chars} characters."
            )

        # 3. Sensitivity ceiling
        if item.sensitivity.rank > self.max_allowed_sensitivity.rank:
            raise PolicyViolationError(
                f"Item sensitivity '{item.sensitivity.value}' exceeds policy maximum "
                f"'{self.max_allowed_sensitivity.value}'."
            )

        # 4. Tenant isolation check
        if self.enforce_strict_tenant_isolation and not item.tenant_id:
            raise PolicyViolationError(
                "Policy requires an explicit tenant_id for all ingested context items."
            )

        # 5. Metadata key inspection for sensitive secrets
        for key in item.metadata:
            if key.lower() in self.forbidden_metadata_keys:
                raise PolicyViolationError(
                    f"Metadata key '{key}' contains prohibited sensitive terminology."
                )

        # 6. Age check if created_at is older than max_context_age
        if self.max_context_age is not None:
            now = utc_now()
            age = now - item.created_at
            if age > self.max_context_age:
                raise PolicyViolationError(
                    f"Item age ({age.total_seconds()}s) exceeds max allowed age of "
                    f"{self.max_context_age.total_seconds()}s."
                )

    def is_query_allowed(self, query: ContextQuery) -> tuple[bool, str | None]:
        """
        Validates if a query satisfies scope and sensitivity rules.
        """
        if self.enforce_strict_tenant_isolation and not query.tenant_id:
            return (
                False,
                "Tenant isolation policy requires an explicit tenant_id in ContextQuery.",
            )
        return True, None

    def filter_item_by_sensitivity(
        self, item: ContextItem, requested_sensitivity: SensitivityLevel | None
    ) -> bool:
        """
        Returns True if item sensitivity does not exceed requested sensitivity ceiling.
        """
        ceiling = requested_sensitivity or self.max_allowed_sensitivity
        return item.sensitivity.rank <= ceiling.rank

    def filter_item_by_metadata(
        self, item: ContextItem, metadata_filter: dict[str, Any] | None
    ) -> bool:
        """
        Returns True if item metadata contains all key-value pairs in metadata_filter.
        """
        if not metadata_filter:
            return True
        for k, v in metadata_filter.items():
            if k not in item.metadata or item.metadata[k] != v:
                return False
        return True
