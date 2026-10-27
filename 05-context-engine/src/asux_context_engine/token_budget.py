import math
import re
from typing import Protocol

from asux_context_engine.models import ContextItem


class TokenCounter(Protocol):
    """Protocol for counting or estimating tokens in textual content."""

    def count_tokens(self, text: str) -> int:
        """Counts or estimates the number of tokens in the given text."""
        ...


class HeuristicTokenCounter:
    """
    Transparent, documented heuristic token estimator.
    Does not require model network calls, GPUs, or proprietary tokenizers.
    Calculates estimated tokens based on character length and word boundaries.
    """

    def __init__(self, chars_per_token: float = 4.0) -> None:
        self.chars_per_token = max(1.0, chars_per_token)

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        char_estimate = math.ceil(len(text) / self.chars_per_token)
        # Word-based estimate: split by whitespace & punctuation
        words = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
        word_estimate = math.ceil(len(words) * 1.3)
        # Conservative approach: take the max of character and word-based estimates
        return max(char_estimate, word_estimate)


class TokenBudgetManager:
    """
    Manages budget allocation and pruning of context items against a target token capacity.
    """

    def __init__(
        self,
        max_budget: int,
        counter: TokenCounter | None = None,
        reserved_budget: int = 0,
    ) -> None:
        if max_budget <= 0:
            raise ValueError("max_budget must be greater than zero.")
        if reserved_budget < 0 or reserved_budget >= max_budget:
            raise ValueError("reserved_budget must be non-negative and less than max_budget.")

        self.max_budget = max_budget
        self.reserved_budget = reserved_budget
        self.usable_budget = max_budget - reserved_budget
        self.counter = counter or HeuristicTokenCounter()

    def count_item_tokens(self, item: ContextItem) -> int:
        """Computes the estimated tokens for a context item (content + metadata keys)."""
        content_tokens = self.counter.count_tokens(item.content)
        # Add small metadata overhead
        meta_str = f"{item.source}:{item.context_type.value}"
        overhead = self.counter.count_tokens(meta_str) + 4
        return content_tokens + overhead

    def fits(self, item: ContextItem, current_tokens: int) -> bool:
        """Returns True if the item can fit within the remaining usable budget."""
        item_tokens = self.count_item_tokens(item)
        return (current_tokens + item_tokens) <= self.usable_budget
