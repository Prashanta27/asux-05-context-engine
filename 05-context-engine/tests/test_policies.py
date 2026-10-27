from datetime import timedelta

import pytest

from asux_context_engine.exceptions import PolicyViolationError
from asux_context_engine.models import (
    ContextItem,
    ContextQuery,
    ContextType,
    SensitivityLevel,
    utc_now,
)
from asux_context_engine.policies import ContextPolicy


def test_policy_content_size_violation(default_policy: ContextPolicy) -> None:
    # max_item_content_chars is 1000 in default_policy
    giant_content = "x" * 1500
    item = ContextItem(content=giant_content, tenant_id="t1")

    with pytest.raises(PolicyViolationError, match="exceeds policy maximum"):
        default_policy.validate_item(item)


def test_policy_forbidden_metadata_keys(default_policy: ContextPolicy) -> None:
    item = ContextItem(
        content="Normal text",
        tenant_id="t1",
        metadata={"api_key": "supersecretkey123"},
    )
    with pytest.raises(PolicyViolationError, match="prohibited sensitive terminology"):
        default_policy.validate_item(item)


def test_policy_tenant_isolation(default_policy: ContextPolicy) -> None:
    # Item missing tenant_id
    item_no_tenant = ContextItem(content="No tenant", tenant_id=None)
    with pytest.raises(PolicyViolationError, match="requires an explicit tenant_id"):
        default_policy.validate_item(item_no_tenant)

    # Query missing tenant_id
    query_no_tenant = ContextQuery(query_text="search", tenant_id=None)
    allowed, reason = default_policy.is_query_allowed(query_no_tenant)
    assert allowed is False
    assert "Tenant isolation policy requires" in (reason or "")


def test_policy_disallowed_type() -> None:
    strict_policy = ContextPolicy(allowed_types=[ContextType.FACTUAL_KNOWLEDGE])
    item = ContextItem(
        content="Instruction", context_type=ContextType.SYSTEM_INSTRUCTION, tenant_id="t1"
    )

    with pytest.raises(PolicyViolationError, match="not allowed by active policy"):
        strict_policy.validate_item(item)


def test_policy_sensitivity_filtering(default_policy: ContextPolicy) -> None:
    public_item = ContextItem(content="Public", tenant_id="t1", sensitivity=SensitivityLevel.PUBLIC)
    restricted_item = ContextItem(
        content="Restricted", tenant_id="t1", sensitivity=SensitivityLevel.RESTRICTED
    )

    # When requesting maximum sensitivity INTERNAL:
    assert default_policy.filter_item_by_sensitivity(public_item, SensitivityLevel.INTERNAL) is True
    assert (
        default_policy.filter_item_by_sensitivity(restricted_item, SensitivityLevel.INTERNAL)
        is False
    )


def test_policy_max_age_violation() -> None:
    age_policy = ContextPolicy(max_context_age=timedelta(days=1))
    now = utc_now()
    old_item = ContextItem(
        content="Old item",
        tenant_id="t1",
        created_at=now - timedelta(days=2),
    )
    with pytest.raises(PolicyViolationError, match="exceeds max allowed age"):
        age_policy.validate_item(old_item)
