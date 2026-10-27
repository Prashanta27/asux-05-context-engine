# Project 5: AsuX Context Engine — Implementation & Compatibility Plan

## 1. Overview and Objectives
The **Context Engine** is the fifth subsystem of the AsuX AI Engineering syllabus. It provides a structured, bounded, and auditable information layer for AI agents. Rather than providing unbounded raw text or arbitrary database queries directly to the LLM, the Context Engine is responsible for:
- Registering, categorizing, and validating context items.
- Scoping information to specific tenants, sessions, and tasks to prevent cross-tenant/cross-user data leakage.
- Transparently ranking candidate items using deterministic multi-factor scoring (relevance, priority, recency, category).
- Enforcing strict token budgets to prevent model context window overflow and unexpected costs.
- Conservative deduplication to avoid redundant prompt clutter.
- Formatting retrieved context with clear untrusted data delimiters so downstream models treat it as data rather than trusted instructions.

## 2. Compatibility Analysis with Existing Projects
- **Project 1 (`asux-llm-gateway`)**:
  - Interface: `Message`, `Role`, `LLMClient`.
  - Integration: Context Engine provides `LLMContextAdapter` to wrap retrieved context items into structured `Message` objects with delimiters.
- **Project 2 (`asux-prompt-engine`)**:
  - Interface: `PromptEngine.render(RenderRequest(variables={...}))`.
  - Integration: The rendered context string can be cleanly supplied to prompt variables (e.g., `context_info` or `catalog_context`).
- **Project 3 (`asux-tool-runtime`)**:
  - Interface: `PermissionContext`, `ToolResult`.
  - Integration: Structured tool outputs from Project 3 can be ingested into Context Engine as `ContextType.TOOL_OUTPUT`, retaining invocation provenance and permission boundaries.
- **Project 4 (`asux-agent-runtime`)**:
  - Interface: `AgentRequest`, `CommerceAssistant`, `AgentLoop`.
  - Integration: `AgentContextAdapter` allows the agent runtime to request relevant context for an incoming `AgentRequest` without modifying the core agent loop.

## 3. Architecture Breakdown
1. **Data Models (`models.py`)**: `ContextItem`, `ContextQuery`, `ContextResult`, `ContextScore`, `ContextType`, `SensitivityLevel`.
2. **Configuration (`config.py`)**: `ContextEngineConfig` for defaults, token limits, TTL, and isolation settings.
3. **Exceptions (`exceptions.py`)**: Explicit, typed exception hierarchy.
4. **Storage Abstraction (`context_store.py`)**: `ContextStore` Protocol + `InMemoryContextStore` with scoped query and safe clear semantics.
5. **Ranking Engine (`context_ranker.py`)**: Deterministic multi-factor scoring combining token/keyword relevance, priority weighting, and recency decay.
6. **Deduplication (`deduplication.py`)**: Exact hash and normalized text matching with conservative metadata retention.
7. **Token Budgeting (`token_budget.py`)**: `TokenCounter` abstraction + documented heuristic token estimator.
8. **Policy Layer (`policies.py`)**: `ContextPolicy` enforcing max items, TTL, content size, sensitivity, and isolation.
9. **Context Assembly (`context_builder.py`)**: Pipeline that queries, filters, deduplicates, ranks, budgets, and formats context with security delimiters.
10. **Facade API (`context_manager.py`)**: Primary user-facing interface for all context operations.
11. **Adapters (`adapters/`)**: Adapters for Agent Runtime and LLM Gateway.

## 4. Security & Safety Strategy
- **Untrusted Context Delimiters**: Formatted context uses explicit delimiters (`=== CONTEXT ITEM: id=... ===`) and security disclaimers so LLMs do not execute prompt injections embedded in context.
- **Tenant & Session Isolation**: All queries and listings strictly enforce tenant isolation; clearing operations cannot accidentally wipe other sessions or global context.
- **Finite Budgets**: Strict token and item limits prevent unbounded context growth.

## 5. Verification Strategy
- 100% automated test suite using `pytest` and `pytest-asyncio`.
- Formatting & linting via `ruff`.
- Strict static typing via `mypy`.
- Practical runnable example scripts.
