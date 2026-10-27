# AsuX Context Engine V1

Production-oriented, bounded, and auditable Context Management Subsystem for the AsuX AI Workforce platform.

---

## 1. Overview
The **AsuX Context Engine** (Project 5) provides a structured, bounded, and auditable context management layer for AI agents. It ensures that an agent receives relevant, deduplicated, and prioritized information while strictly respecting token budgets and security boundaries.

## 2. Key Features
- **Data Models:** Typed, timezone-aware `ContextItem`, `ContextQuery`, and `ContextResult` with Pydantic v2 validation.
- **Strict Scope Isolation:** Multi-tenant and session-scoped indexing to prevent cross-tenant information leakage.
- **Deterministic Multi-Factor Ranking:** Transparent scoring combining token overlap, explicit priority weighting, and recency decay.
- **Conservative Deduplication:** Exact SHA-256 and normalized Unicode/whitespace duplicate detection with metadata merging.
- **Token Budgeting:** Bounded assembly preventing model context window overflows using documented heuristic estimation.
- **Security Boundaries:** Delimited formatting framing retrieved information as untrusted external data.
- **Adapters:** Out-of-the-box adapters for Project 1 (`asux-llm-gateway`) and Project 4 (`asux-agent-runtime`).

---

## 3. Architecture

```text
User / Agent Request
       ↓
AgentContextAdapter
       ↓
 ContextManager (Facade)
   ├── ContextPolicy (Validation & Tenant Scope)
   ├── ContextStore (InMemory / Pluggable Protocol)
   └── ContextBuilder
         ├── ContextDeduplicator
         ├── ContextRanker
         ├── TokenBudgetManager
         └── Delimited Formatter
       ↓
 Structured ContextResult
```

---

## 4. Installation & Setup

```powershell
cd C:\Users\HP\.gemini\antigravity\scratch\05-context-engine

# Create virtual environment and install dependencies in editable mode:
python -m venv .venv
.\.venv\Scripts\pip install -e ..\asux-llm-gateway
.\.venv\Scripts\pip install -e ..\02-prompt-engine
.\.venv\Scripts\pip install -e ..\03-tool-runtime
.\.venv\Scripts\pip install -e ..\04-agent-runtime
.\.venv\Scripts\pip install -e .[dev]
```

---

## 5. Quick-Start Example

```python
from asux_context_engine import ContextManager, ContextItem, ContextQuery, ContextType

# 1. Initialize Context Manager
cm = ContextManager()

# 2. Add Context Items
cm.add_item(
    ContextItem(
        content="Customer has 500 reward points and preferred tier Gold.",
        context_type=ContextType.FACTUAL_KNOWLEDGE,
        source="crm",
        tenant_id="tenant_001",
        priority=8,
    )
)

# 3. Retrieve and Assemble Context
query = ContextQuery(
    query_text="reward points tier",
    tenant_id="tenant_001",
    token_budget=1000,
)
result = cm.build_context(query)

print("Selected items:", len(result.items))
print("Formatted Context:\n", result.formatted_context)
```

---

## 6. Running Tests and Checks

```powershell
# Run Pytest suite:
.\.venv\Scripts\pytest

# Run Linter & Formatter:
.\.venv\Scripts\ruff format .
.\.venv\Scripts\ruff check --fix .

# Run Type Checking:
.\.venv\Scripts\mypy src
```
