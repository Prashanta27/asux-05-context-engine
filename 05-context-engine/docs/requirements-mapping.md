# Requirements Mapping: AsuX Context Engine

> **Note on Syllabus Availability:** An external standalone syllabus file was not discovered in the local workspace directory. As instructed by Project Guidelines (Section 3), this baseline architecture implements the core Project 5 requirements specified in the project prompt, and this limitation is explicitly noted.

| Requirement Area | Specification / Behavior | Implementation Component | Source Files | Verifying Tests | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Models** | Typed, timezone-aware, validated models for items, queries, and results | `ContextItem`, `ContextQuery`, `ContextResult`, `ContextScore`, `ContextType`, `SensitivityLevel` | `src/asux_context_engine/models.py` | `tests/test_models.py` | Complete |
| **Exceptions & Errors** | Explicit typed exceptions for items not found, policy violations, budget overflow, scope errors | `ContextEngineError` hierarchy | `src/asux_context_engine/exceptions.py` | `tests/test_models.py`, `tests/test_context_manager.py` | Complete |
| **Storage Abstraction** | Protocol and In-memory storage with scoped add, get, update, delete, list, clear, and expire | `ContextStore`, `InMemoryContextStore` | `src/asux_context_engine/context_store.py` | `tests/test_context_store.py` | Complete |
| **Deterministic Ranking** | Multi-factor scoring combining text relevance, priority weighting, recency decay, and type weight | `ContextRanker` | `src/asux_context_engine/context_ranker.py` | `tests/test_context_ranker.py` | Complete |
| **Context Deduplication** | Conservative duplicate detection (exact and normalized text) without losing unique metadata | `ContextDeduplicator` | `src/asux_context_engine/deduplication.py` | `tests/test_deduplication.py` | Complete |
| **Token Budgeting** | Bounded token allocation, budget management, and documented heuristic token counting | `TokenCounter`, `HeuristicTokenCounter`, `TokenBudgetManager` | `src/asux_context_engine/token_budget.py` | `tests/test_token_budget.py` | Complete |
| **Context Policies** | Configurable policies for allowed categories, item count, TTL expiration, and sensitivity | `ContextPolicy` | `src/asux_context_engine/policies.py` | `tests/test_policies.py` | Complete |
| **Context Assembly** | Retrieval, deduplication, ranking, budget pruning, and delimited untrusted formatting | `ContextBuilder` | `src/asux_context_engine/context_builder.py` | `tests/test_context_builder.py` | Complete |
| **Public Management API**| Unified facade for adding, updating, retrieving, clearing, and building context | `ContextManager` | `src/asux_context_engine/context_manager.py` | `tests/test_context_manager.py` | Complete |
| **Security & Untrusted Data**| Delimited formatting, prompt injection defense, tenant and session isolation enforcement | `ContextBuilder._format_delimited()`, `ContextPolicy.validate_scope()` | `src/asux_context_engine/context_builder.py`, `policies.py` | `tests/test_policies.py`, `tests/test_integration.py` | Complete |
| **Agent Runtime Adapter**| Integration with Project 4 (`asux-agent-runtime`) for automated context provisioning | `AgentContextAdapter` | `src/asux_context_engine/adapters/agent_adapter.py` | `tests/test_integration.py` | Complete |
| **LLM Gateway Adapter** | Integration with Project 1 (`asux-llm-gateway`) Message format with delimiter tags | `LLMContextAdapter` | `src/asux_context_engine/adapters/llm_adapter.py` | `tests/test_integration.py` | Complete |
