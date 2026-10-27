# Testing Strategy: AsuX Context Engine

## 1. Test Suite Coverage

The test suite covers:
- **Models (`test_models.py`)**: Item creation, timezone-awareness validation, expiration logic, query constraints, result models.
- **Context Store (`test_context_store.py`)**: Add, get, update, delete, thread-safety, list filtering by scope, safe clear operations, and stale item expiration.
- **Ranker (`test_context_ranker.py`)**: Multi-factor ranking, token overlap calculations, recency decay over time, explicit priority weights, and empty-query behavior.
- **Deduplication (`test_deduplication.py`)**: Exact text matching, Unicode NFKC normalization, whitespace collapsing, case insensitivity, and conservative metadata merging.
- **Token Budget (`test_token_budget.py`)**: Heuristic token counting accuracy, word-based and character-based fallback, boundary enforcement, and item pruning.
- **Policies (`test_policies.py`)**: Content length limits, allowed context types, secret metadata rejection, tenant isolation enforcement, and sensitivity filtering.
- **Context Builder (`test_context_builder.py`)**: End-to-end assembly, budget adherence, warnings generation, and delimited formatting.
- **Context Manager (`test_context_manager.py`)**: Facade API integration, updating non-existent items, scoped clearance, and query authorization.
- **System Integration (`test_integration.py`)**: Integration with Project 1 (`asux-llm-gateway`) and Project 4 (`asux-agent-runtime`).

## 2. Deterministic Testing
- Tests do not require external network connections, paid APIs, or GPU hardware.
- Timezone-aware datetimes with fixed offsets ensure repeatable expiration and recency tests.
