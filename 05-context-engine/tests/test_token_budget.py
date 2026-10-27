import pytest

from asux_context_engine.models import ContextItem
from asux_context_engine.token_budget import HeuristicTokenCounter, TokenBudgetManager


def test_token_counter_empty_and_text() -> None:
    counter = HeuristicTokenCounter(chars_per_token=4.0)
    assert counter.count_tokens("") == 0
    # "Hello world" is 11 chars (3 tokens by char) and 2 words (3 tokens by word)
    count = counter.count_tokens("Hello world")
    assert count >= 3


def test_budget_manager_bounds_validation() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        TokenBudgetManager(max_budget=0)

    with pytest.raises(ValueError, match="reserved_budget"):
        TokenBudgetManager(max_budget=100, reserved_budget=100)


def test_budget_manager_item_fitting(token_budget_manager: TokenBudgetManager) -> None:
    # Usable budget is 500
    small_item = ContextItem(content="Short content", tenant_id="t1")
    tokens = token_budget_manager.count_item_tokens(small_item)
    assert tokens > 0
    assert token_budget_manager.fits(small_item, current_tokens=0) is True

    # Item doesn't fit if current_tokens + item_tokens > 500
    assert token_budget_manager.fits(small_item, current_tokens=495) is False
