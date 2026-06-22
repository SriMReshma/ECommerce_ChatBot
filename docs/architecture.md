# eComBot Architecture

```mermaid
flowchart LR
    U["Customer"] --> C["Chainlit UI"]
    P["Promptfoo"] --> API["FastAPI /chat"]
    C --> R["Shared Capstone Runtime"]
    API --> R
    R --> G{"Runtime mode"}
    G -->|deterministic| O["Offline Orchestrator"]
    G -->|adk| ADK["Google ADK Runner"]
    G -->|litellm| LLM["LiteLLM completion + fallback"]
    ADK --> SA["Support ADK Agent"]
    ADK --> SLA["Sales ADK Agent"]
    O --> S["Support Agent"]
    O --> SL["Sales Agent / ReAct"]
    S --> MCP["FastMCP Client"]
    SA --> MCP
    MCP --> MT["Order and Inventory MCP Tools"]
    SL --> LC["LangChain Runnable + StructuredTools"]
    SLA --> LC
    LC --> CH["ChromaDB"]
    CH --> KB["Products + FAQ + PDF chunks"]
    MT --> PG["PostgreSQL business data"]
    R --> REDIS["Redis session snapshots"]
    R --> HIST["PostgreSQL conversation history"]
    R --> LS["LangSmith traces"]
    R --> JL["Local JSONL traces"]
```

## Execution Guarantees

- Deterministic mode is offline, grounded, repeatable, and used by CI.
- Live ADK and LiteLLM modes are enabled only when explicitly selected and supplied with model keys.
- Redis and PostgreSQL are strict active backends in Compose; local runs use configured fallbacks.
- Chroma retrieval rejects low-confidence nearest neighbors before agents can use them.
- Promptfoo and Chainlit call the same runtime contract, preventing evaluation-only behavior.
