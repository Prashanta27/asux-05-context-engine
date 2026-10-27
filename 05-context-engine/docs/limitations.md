# Known Limitations and Assumptions

1. **In-Memory Storage Backend**: The baseline implementation provides an `InMemoryContextStore`. While thread-safe and isolated, items do not survive process restarts. Production persistence will require a SQL or document database backend implementing the `ContextStore` protocol.
2. **Lexical Keyword / Token Matching**: The default `ContextRanker` relies on deterministic token overlap, priority, and recency scoring. It does not use neural embedding models or vector databases (which belong to Project 7 Knowledge Engine / RAG).
3. **Heuristic Token Counting**: The default `HeuristicTokenCounter` uses character and word estimation formulas ($1 \text{ token} \approx 4 \text{ chars}$ or $1.3 \times \text{words}$). It provides a reliable upper bound without model dependencies, but is not an exact model BPE tokenizer.
4. **Prompt Injection Limitations**: While delimited formatting clearly demarcates untrusted data for LLMs, formatting alone cannot prevent advanced jailbreaks if the downstream model lacks system instruction adherence.
5. **Syllabus File Availability**: As noted in `requirements-mapping.md`, the syllabus was not available as a physical file in the local workspace; hence, requirements were mapped against the Project 5 specification in the master prompt.
