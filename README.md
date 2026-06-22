# ecombot_Capstone_GoogleADK_Chainlit

Production-oriented Google ADK capstone for an electronics ecommerce assistant. The same domain runtime powers Chainlit, a FastAPI evaluation endpoint, local tests, Promptfoo, and optional live ADK/LiteLLM execution.

## Integrated Stack

| Capability | Active implementation |
|---|---|
| Google ADK | Real `LlmAgent` orchestrator with Support and Sales sub-agents in `src/adk/agents.py`; `agent.py` is the ADK Web entrypoint |
| LangChain | `RunnableLambda`, `StructuredTool`, and `Document` abstractions over the grounded retrieval/tool layer |
| RAG | Product, FAQ, and PDF chunks indexed in ChromaDB with deterministic local embeddings and confidence filtering |
| LiteLLM | Live completion adapter, primary/fallback handling, and an optional OpenAI/OpenRouter proxy profile |
| FastMCP | Real FastMCP server and client; container mode invokes tools through the in-process MCP transport |
| Session memory | Redis snapshots with a 24-hour TTL; in-memory fallback for no-service runs |
| Durable history | PostgreSQL turn history, metadata, tool calls, and indexed session retrieval |
| Observability | LangSmith `traceable` execution when configured, plus always-on local JSONL traces |
| Evaluation | 12 Promptfoo HTTP cases mirrored by pytest contract tests |
| UI | Chainlit product/order elements, source tags, model/cost badge, blocked indicator, and reopenable debug sidebar |
| Security | Input injection checks, output PII filtering, competitor filtering, and validated tool inputs |
| Voice | Optional faster-whisper STT and Piper TTS using the same runtime |
| CI/CD | GitHub Actions runs index build, pytest, Promptfoo, and Docker image build |

See [docs/architecture.md](docs/architecture.md) for the end-to-end flow.

## Runtime Modes

- `deterministic` is the default. It uses grounded local logic and requires no model key.
- `litellm` runs the grounded draft through `litellm.completion` with automatic fallback.
- `adk` runs the real Google ADK `Runner` and its specialist agents.

Live modes require `OPENROUTER_API_KEY`. LangSmith upload requires `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`.

## Local Run

```powershell
cd C:\Users\rmt032\Downloads\ecombot_Capstone_GoogleADK_Chainlit
python -m pip install -r requirements.txt
python -m src.rag.embed_catalog
python -m pytest -q -p no:cacheprovider
python run_ui.py
```

Open `http://localhost:8000`.

Start the evaluation API separately:

```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001
```

## Google ADK Web

Set a model key and select live ADK mode:

```powershell
$env:OPENROUTER_API_KEY="your-key"
$env:ECOMBOT_RUNTIME_MODE="adk"
adk web --port 8002 .
```

Open `http://localhost:8002` and select `ecombot_orchestrator`.

## Rancher Desktop

Rancher Desktop must use `dockerd (moby)`. Resolve the redirected Desktop path and start Chainlit, API, Redis, and PostgreSQL:

```powershell
$project = Join-Path ([Environment]::GetFolderPath("Desktop")) "ecombot_Capstone_GoogleADK_Chainlit"
Set-Location $project
docker compose up --build -d
docker compose ps
```

- Chainlit: `http://localhost:8000`
- API health: `http://localhost:8001/health`
- PostgreSQL host port: `5433`
- Redis host port: `6380`

Start the optional LiteLLM proxy:

```powershell
$env:OPENAI_API_KEY="your-openai-key"
$env:OPENROUTER_API_KEY="your-openrouter-key"
docker compose --profile litellm up -d litellm
```

Stop without deleting database volumes:

```powershell
docker compose down
```

## Promptfoo

With the evaluation API running at port `8001`:

```powershell
npm install
$env:PROMPTFOO_API_BASE_URL="http://127.0.0.1:8001"
npm run eval
```

Or run Promptfoo entirely through Compose:

```powershell
docker compose --profile eval run --rm promptfoo
```

The suite is in `evals/promptfooconfig.yaml` and covers support, sales, RAG, unknown products, MCP errors, three injection attacks, inventory, and reflection.

## FastMCP

Container mode uses the in-process FastMCP transport. To run a standalone HTTP MCP server:

```powershell
$env:MCP_TRANSPORT="http"
python -m src.services.mcp_backend.server
```

Set `MCP_URL=http://127.0.0.1:8775/mcp` for the client.

## Voice

Install optional local voice dependencies:

```powershell
python -m pip install -r requirements-optional.txt
```

Configure `WHISPER_MODEL`, `WHISPER_DEVICE`, and `PIPER_MODEL`. Without a Piper model, text flows continue and TTS reports its local fallback instead of fabricating audio.

## Main Structure

```text
agent.py                         Google ADK Web root agent
evals/promptfooconfig.yaml       Promptfoo regression suite
src/adk/                         ADK agents and Runner adapter
src/api/                         FastAPI chat/evaluation endpoint
src/agents/                      Deterministic offline agents
src/gateway/                     Routing and live LiteLLM execution
src/integrations/                LangChain StructuredTools
src/observability/               LangSmith and JSONL tracing
src/rag/                         PDF ingestion, LangChain, ChromaDB
src/runtime/                     Shared persisted execution engine
src/services/                    Redis, PostgreSQL, FastMCP
src/ui/                          Chainlit UI
src/voice/                       faster-whisper/Piper pipeline
tests/                           Unit and integration tests
```

## Documentation PDF

```powershell
python scripts/generate_documentation_pdf.py
```

The output is `docs/ecombot_capstone_functionality.pdf`.
