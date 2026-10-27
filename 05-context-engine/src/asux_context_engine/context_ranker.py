import math
import re
from datetime import UTC, datetime

from asux_context_engine.models import (
    ContextItem,
    ContextQuery,
    ContextScore,
    utc_now,
)


class ContextRanker:
    """
    Transparent, deterministic multi-factor context ranker.
    Combines text relevance, explicit priority, recency decay, and type importance.
    """

    def __init__(
        self,
        weight_relevance: float = 0.50,
        weight_priority: float = 0.30,
        weight_recency: float = 0.20,
        recency_half_life_hours: float = 24.0,
        min_relevance_threshold: float = 0.05,
    ) -> None:
        self.weight_relevance = weight_relevance
        self.weight_priority = weight_priority
        self.weight_recency = weight_recency
        self.recency_half_life_hours = recency_half_life_hours
        self.min_relevance_threshold = min_relevance_threshold

    @classmethod
    def tokenize(cls, text: str) -> set[str]:
        """Extracts unique lowercase alphanumeric tokens from text."""
        return set(re.findall(r"\b\w{2,}\b", text.lower()))

    def compute_text_relevance(self, query_tokens: set[str], item: ContextItem) -> float:
        """
        Computes token overlap relevance between query tokens and item content/metadata.
        Returns a score in [0.0, 1.0].
        """
        if not query_tokens:
            return 1.0  # If no query specified, text relevance does not penalize items

        content_tokens = self.tokenize(item.content)
        # Check metadata values if string
        for val in item.metadata.values():
            if isinstance(val, str):
                content_tokens.update(self.tokenize(val))

        if not content_tokens:
            return 0.0

        matches = query_tokens.intersection(content_tokens)
        overlap_ratio = len(matches) / len(query_tokens)
        return min(1.0, overlap_ratio)

    def compute_priority_score(self, priority: int) -> float:
        """Normalizes integer priority (0-100) into a [0.0, 1.0] range."""
        clamped = max(0, min(100, priority))
        return clamped / 100.0

    def compute_recency_score(self, created_at: datetime, now: datetime) -> float:
        """
        Computes an exponential recency decay score in [0.0, 1.0]
        based on the configured half-life in hours.
        """
        diff_seconds = max(0.0, (now - created_at).total_seconds())
        diff_hours = diff_seconds / 3600.0
        # Exponential decay: 0.5 ** (diff_hours / half_life)
        decay = math.pow(0.5, diff_hours / max(0.1, self.recency_half_life_hours))
        return max(0.0, min(1.0, decay))

    def rank(
        self,
        query: ContextQuery,
        candidates: list[ContextItem],
        now: datetime | None = None,
    ) -> list[ContextScore]:
        """
        Ranks candidate ContextItems against a query.
        Filters out expired items and items below the relevance threshold.
        """
        current_time = now if now is not None else utc_now()
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=UTC)

        query_tokens = self.tokenize(query.query_text) if query.query_text else set()
        scores: list[ContextScore] = []

        for item in candidates:
            # Exclude expired items
            if item.is_expired(current_time):
                continue

            rel_score = self.compute_text_relevance(query_tokens, item)
            # If a specific query_text was provided and relevance is zero/below threshold, skip
            if query_tokens and rel_score < self.min_relevance_threshold:
                continue

            prio_score = self.compute_priority_score(item.priority)
            rec_score = self.compute_recency_score(item.created_at, current_time)

            total_score = (
                (self.weight_relevance * rel_score)
                + (self.weight_priority * prio_score)
                + (self.weight_recency * rec_score)
            )

            breakdown = {
                "relevance": round(rel_score, 4),
                "priority": round(prio_score, 4),
                "recency": round(rec_score, 4),
                "composite": round(total_score, 4),
            }

            scores.append(
                ContextScore(
                    item=item,
                    score=total_score,
                    breakdown=breakdown,
                )
            )

        # Deterministic sort: score desc, priority desc, recency desc, id asc
        scores.sort(
            key=lambda cs: (
                -cs.score,
                -cs.item.priority,
                -cs.item.created_at.timestamp(),
                cs.item.id,
            )
        )

        return scores[: query.limit]
