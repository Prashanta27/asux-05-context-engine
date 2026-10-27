from datetime import timedelta

from asux_context_engine.context_ranker import ContextRanker
from asux_context_engine.models import ContextItem, ContextQuery, utc_now


def test_ranker_text_relevance(ranker: ContextRanker) -> None:
    now = utc_now()
    item_relevant = ContextItem(
        content="Laptop warranty covers hardware defects.",
        tenant_id="t1",
        created_at=now,
        priority=5,
    )
    item_irrelevant = ContextItem(
        content="Cooking recipes for healthy dinner.",
        tenant_id="t1",
        created_at=now,
        priority=5,
    )

    query = ContextQuery(query_text="laptop warranty hardware", tenant_id="t1")
    scores = ranker.rank(query, [item_relevant, item_irrelevant], now=now)

    assert len(scores) == 1
    assert scores[0].item.id == item_relevant.id
    assert scores[0].breakdown["relevance"] > 0.5


def test_ranker_priority_weighting(ranker: ContextRanker) -> None:
    now = utc_now()
    item_low_prio = ContextItem(
        content="General notice about store hours.",
        tenant_id="t1",
        created_at=now,
        priority=2,
    )
    item_high_prio = ContextItem(
        content="Urgent notice about store hours.",
        tenant_id="t1",
        created_at=now,
        priority=90,
    )

    query = ContextQuery(query_text="store hours", tenant_id="t1")
    scores = ranker.rank(query, [item_low_prio, item_high_prio], now=now)

    assert len(scores) == 2
    # High priority item should rank first
    assert scores[0].item.id == item_high_prio.id
    assert scores[0].score > scores[1].score


def test_ranker_recency_decay(ranker: ContextRanker) -> None:
    now = utc_now()
    item_recent = ContextItem(
        content="Policy update for customer discounts.",
        tenant_id="t1",
        created_at=now - timedelta(minutes=10),
        priority=5,
    )
    item_old = ContextItem(
        content="Policy update for customer discounts.",
        tenant_id="t1",
        created_at=now - timedelta(days=7),
        priority=5,
    )

    query = ContextQuery(query_text="customer discounts", tenant_id="t1")
    scores = ranker.rank(query, [item_old, item_recent], now=now)

    assert len(scores) == 2
    assert scores[0].item.id == item_recent.id
    assert scores[0].breakdown["recency"] > scores[1].breakdown["recency"]


def test_ranker_excludes_expired_items(ranker: ContextRanker) -> None:
    now = utc_now()
    expired = ContextItem(
        content="Special promotion code PROMO10.",
        tenant_id="t1",
        created_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
        priority=100,
    )
    active = ContextItem(
        content="Special promotion code PROMO20.",
        tenant_id="t1",
        created_at=now,
        priority=5,
    )

    query = ContextQuery(query_text="promotion code", tenant_id="t1")
    scores = ranker.rank(query, [expired, active], now=now)

    assert len(scores) == 1
    assert scores[0].item.id == active.id


def test_ranker_empty_query(ranker: ContextRanker) -> None:
    now = utc_now()
    item1 = ContextItem(content="First", tenant_id="t1", priority=10, created_at=now)
    item2 = ContextItem(content="Second", tenant_id="t1", priority=80, created_at=now)

    query = ContextQuery(query_text="", tenant_id="t1")
    scores = ranker.rank(query, [item1, item2], now=now)

    assert len(scores) == 2
    assert scores[0].item.id == item2.id
