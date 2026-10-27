from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from asux_context_engine.models import (
    ContextItem,
    ContextQuery,
    ContextResult,
    ContextType,
    SensitivityLevel,
)


def test_context_item_valid(now: datetime) -> None:
    item = ContextItem(
        content="Valid context content.",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        source="test",
        created_at=now,
        priority=10,
    )
    assert item.content == "Valid context content."
    assert item.priority == 10
    assert item.created_at.tzinfo is not None
    assert item.is_expired() is False


def test_context_item_empty_content_rejected() -> None:
    with pytest.raises(ValidationError):
        ContextItem(content="   ", context_type=ContextType.FACTUAL_KNOWLEDGE)

    with pytest.raises(ValidationError):
        ContextItem(content="", context_type=ContextType.FACTUAL_KNOWLEDGE)


def test_context_item_expiration_validation(now: datetime) -> None:
    # expires_at <= created_at must raise ValidationError
    with pytest.raises(ValidationError):
        ContextItem(
            content="Expired item",
            created_at=now,
            expires_at=now - timedelta(seconds=1),
        )

    # Valid expiration in the future
    future_item = ContextItem(
        content="Future item",
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )
    assert future_item.is_expired(now) is False
    assert future_item.is_expired(now + timedelta(hours=2)) is True


def test_sensitivity_level_ranking() -> None:
    assert SensitivityLevel.PUBLIC.rank < SensitivityLevel.INTERNAL.rank
    assert SensitivityLevel.INTERNAL.rank < SensitivityLevel.CONFIDENTIAL.rank
    assert SensitivityLevel.CONFIDENTIAL.rank < SensitivityLevel.RESTRICTED.rank


def test_context_query_validation() -> None:
    q = ContextQuery(query_text="search query", limit=20, token_budget=500)
    assert q.limit == 20
    assert q.token_budget == 500

    # Limit must be > 0 and <= 100
    with pytest.raises(ValidationError):
        ContextQuery(limit=0)
    with pytest.raises(ValidationError):
        ContextQuery(limit=101)


def test_context_result_model(sample_item: ContextItem) -> None:
    res = ContextResult(
        items=[sample_item],
        total_tokens_estimated=25,
        budget_limit=100,
        warnings=["Sample warning"],
    )
    assert len(res.items) == 1
    assert res.total_tokens_estimated == 25
    assert len(res.warnings) == 1
