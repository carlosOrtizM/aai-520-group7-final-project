# Architecture

AAI-520 Group 7 — Multi-Agent Financial Advisor

This document is the canonical reference for how the project is built,
why the pieces are split the way they are, and how to extend it. The
end-user `README.md` covers install and run; this file covers
*decisions*. If a convention here conflicts with code, the code is
wrong — open a PR.

---

## 1. Overview

A two-service, hypermedia-driven financial research copilot. A user
asks questions in a chat UI, and an agent service answers either by
RAG over Apple's 10-K, by classifying live market news, by pulling
price history, or by looking up upcoming earnings. The LLM stack is
local (Ollama) so the project runs without paid API keys. The vector
store is local (Chroma) so it survives restarts without external infra.

There is no Docker. There is no Streamlit. There is no Gradio.
A previous teammate scaffolded a Docker + Streamlit variant; that path
is **not** the one we maintain — see §10 for what to keep vs. ignore
in the repo.

---

## 2. Two-service split

```
┌─────────────────────┐    aiohttp / JSON     ┌──────────────────────┐
│  UI service         │ ───────────────────▶  │  Agent service       │
│  FastHTML + htmx    │                       │  FastAPI + LangGraph │
│  port 8010          │ ◀───────────────────  │  port 8011           │
└─────────────────────┘                       └──────────────────────┘
        ▲                                              ▲
        │ browser (htmx swaps,                         │ Ollama, Chroma,
        │ no JS framework)                             │ Finnhub, yfinance
        ▼                                              ▼
   user                                          local LLM + tools
```

### Why two services and not one

- **Independent lifecycles.** Restarting the UI shouldn't drop the
  in-memory LangGraph singletons. Restarting the agent (e.g. after
  swapping Ollama models) shouldn't kill the chat session.
- **Clear ownership boundary.** UI knows nothing about LangGraph,
  Chroma, or Finnhub. Agent knows nothing about htmx or MonsterUI.
  They share exactly one Pydantic model: `ServiceRequest`.
- **Mirror the covered_caller prototype.** That codebase already
  proved the two-service Popen-launcher pattern works on a Raspberry
  Pi without Docker. We're cribbing the same shape so anyone who has
  worked on covered_caller can read this repo immediately.

### The shared contract

```python
# src/utils.py
class ServiceRequest(BaseModel):
    data: dict   = Field(default_factory=dict)  # payload
    params: dict = Field(default_factory=dict)  # metadata
```

Every UI → agent call packs into this shape. Every FastAPI route on
the agent side accepts a `ServiceRequest` body, calls `unpack_request`,
then reads from `req.data` / `req.params`. We don't proliferate
endpoint-specific models — keep the contract dumb and let the handlers
be smart.

### Inter-service transport

`aiohttp.ClientSession` POSTing JSON. Sessions are short-lived
(per call) — no shared session pool. The agent service is `localhost`
only; if we ever expose it, the URL belongs in an env var, not a
hardcoded string. Today it lives in `src/ui/ui_utils.py::AGENT_BASE_URL`.

---

## 3. Directory layout

```
agent-advisor/
├── main.py                    # Popen launcher (spawns both services)
├── pyproject.toml             # slim base deps + [full] extra
├── ARCHITECTURE.md            # this file
├── README.md                  # install + run for newcomers
├── .env                       # API keys + model names (NEVER commit real keys)
│
├── src/                       # the only code that ships
│   ├── __init__.py
│   ├── utils.py               # ServiceRequest, create_logger, log_call
│   │
│   ├── agent/                 # FastAPI service — :8011
│   │   ├── app.py             # routes
│   │   ├── agent_utils.py     # unpack_request, validate_*
│   │   ├── llm_loader.py      # cached ChatOllama client
│   │   ├── chroma_store.py    # persistent Chroma + ingest
│   │   ├── pdf_loader.py      # PDF → langchain Document chunks
│   │   ├── rag_graph.py       # LangGraph RAG (10-K Q&A)
│   │   ├── market_news.py     # Finnhub + sentiment/category/bullets graph
│   │   ├── price_history.py   # yfinance + optional TA-Lib
│   │   └── earnings_calendar.py
│   │
│   └── ui/                    # FastHTML service — :8010
│       ├── app.py             # @rt routes
│       ├── ui_components.py   # MonsterUI components (no logic)
│       ├── ui_handler.py      # aiohttp bridge to agent
│       └── ui_utils.py        # pack_request, send_to_agent
│
├── persistence/               # local state (NOT code)
│   ├── reference_files/       # source PDFs (e.g. AAPL 10-K)
│   ├── chroma/                # persistent vector store (gitignored)
│   └── file_outputs/          # rendered diagrams, screenshots
│
├── logs/                      # per-service log files (auto-rotated daily)
│
├── final-project-ipynbs/      # original deliverable notebooks (reference)
├── g(old)/                    # archived modules (source of truth before src/)
└── financial_system.pdf       # course reference material
```

### Three folders, three roles

- **`src/`** — what ships. Anything imported at runtime lives here.
- **`final-project-ipynbs/` and `g(old)/`** — historical reference.
  Not imported anywhere in `src/`. Kept so we can trace where each
  module came from and so the original notebook deliverables stay
  intact for grading.
- **`persistence/`** — runtime state. Chroma DB is gitignored; the
  source PDFs in `reference_files/` are tracked.

If you need to look at the old code, read it from `g(old)/` — don't
import it. The new code under `src/` is the only thing the services
load.

---

## 4. Agent service routes

| Route        | Method | Body / Params                          | Returns                         |
|--------------|--------|----------------------------------------|---------------------------------|
| `/health`    | GET    | —                                      | liveness probe                  |
| `/chat`      | POST   | `data.query`                           | RAG answer                      |
| `/news`      | POST   | `data.category`, `params.limit`        | per-article + aggregate stats   |
| `/prices`    | POST   | `data.symbol`, `params.window_days`    | OHLCV (+ TA if talib installed) |
| `/earnings`  | POST   | `data.ticker`, `params.lookahead_days` | Finnhub earnings calendar       |
| `/ingest`    | POST   | —                                      | PDF → Chroma chunk count        |

Every route returns `{"error": "..."}` on failure, never an HTTP 5xx.
The UI renders the error inline.

---

## 5. UI service routes

| Route             | Method | Triggers                             |
|-------------------|--------|--------------------------------------|
| `/`               | GET    | launcher screen                      |
| `/chat`           | GET    | full chat screen + sidebar           |
| `/send`           | POST   | submit chat message → htmx beforeend |
| `/tools/news`     | GET    | render news card                     |
| `/tools/prices`   | GET    | render prices card                   |
| `/tools/earnings` | GET    | render earnings card                 |
| `/tools/ingest`   | POST   | render ingest result                 |

`@rt` handlers do three things only: ingest user input, call a handler
in `ui_handler.py`, return a component from `ui_components.py`. Any
`@rt` longer than ~15 lines is a smell — push the work into the
handler or break the component out.

---

## 6. Conventions

### Hypermedia first, no JS framework

We use FastHTML + MonsterUI. htmx ships with FastHTML for DOM swaps
(`hx-target`, `hx-swap`, `hx-trigger`). No React, no Vue, no
Streamlit, no Gradio. If a feature seems to need a JS framework, push
back — we can almost certainly do it with `hx-target="#x"
hx-swap="outerHTML"` and a server-rendered partial.

### Lazy imports for heavy deps

The agent service imports `langchain`, `langgraph`, `chromadb`,
`yfinance`, `finnhub-python`, etc. **only inside route handlers** (or
inside the loader functions they delegate to). The top of
`src/agent/app.py` imports nothing heavier than FastAPI + utils. This
means:

- `python main.py` boots both services even when only the slim base
  deps are installed.
- A missing dep surfaces as `{"error": "..."}` on one route, not a
  startup crash that breaks every route.
- New developers can clone, `pip install -e .`, see the chat screen,
  and then install `.[full]` when they're ready to actually run RAG.

### Caching with module-level singletons

LLM clients, vector stores, and compiled LangGraphs are expensive to
build and stateless to call. Each loader (`get_llm_client`,
`get_vector_store`, `get_rag_graph`, `_build_graph` in `market_news`)
caches its result in a module-level `_SINGLETON` so the second call is
a dict lookup. This is fine because each service runs in a single
process — no cross-process cache invalidation to worry about.

### Error handling

Every `@rt` and every `@app.{post,get}` is wrapped in try/except.
Caught exceptions log to the per-service logger at ERROR level and
return a friendly fallback (an error card on the UI side, an `error`
key on the agent side). We do **not** propagate raw exceptions to the
client.

The custom logger (`create_logger` in `src/utils.py`) writes INFO+ to
`logs/<service>_<date>.txt` and ERROR+ to console. Stale logs (>24h)
are pruned on logger creation. There is no rotation library, no log
shipping — keep it boring.

### No tests, by design

This is a capstone project. We use happy-path smoke testing
(`curl /health`, click through the chat screen) instead of pytest.
If a route breaks on the happy path, fix it; don't write a test
matrix. **Do not** add a `tests/` directory unless the team agrees
the tradeoff has changed.

### What NOT to do

- Don't add Docker. The previous Docker + Streamlit work in the
  project history was a teammate's parallel branch — it is **not**
  the architecture we're shipping.
- Don't add a database. Chroma is the only persistent store. State
  that doesn't fit there belongs in env vars or config files.
- Don't add CDN-loaded fonts/JS. FastHTML serves everything locally.
- Don't add backwards-compat shims for `g(old)/` imports. Anything
  worth keeping has been ported into `src/`; the rest is reference.
- Don't write multi-paragraph docstrings. One sentence per function
  unless there's a non-obvious why.

---

## 7. Agent inventory & consolidation

### Teacher feedback: redundant agents

The original notebook deliverable had **seven** agents/workflows.
Reading them side-by-side confirms the feedback: the four "news"
notebooks overlap heavily. Below is the full inventory, what was
ported, and what we're dropping.

| Notebook                      | Purpose                                                     | Source        | Status in `src/`          |
|-------------------------------|-------------------------------------------------------------|---------------|---------------------------|
| `rag_bot.ipynb`               | RAG over AAPL 10-K via Chroma                               | local PDF     | **Ported** → `rag_graph.py` |
| `market_news_provider.ipynb`  | Finnhub news + sentiment/category/bullets graph             | Finnhub       | **Ported** → `market_news.py` |
| `news_aggregator_chain.ipynb` | Orchestrator-worker research planner over DuckDuckGo        | DuckDuckGo    | **Port pending** (see below) |
| `price_history_provider.ipynb`| yfinance OHLCV + TA-Lib indicators                          | yfinance      | **Ported** → `price_history.py` |
| `earnings_calendar_provider.ipynb` | Finnhub earnings calendar lookup                       | Finnhub       | **Ported** → `earnings_calendar.py` |
| `stock_news_deep_provider.ipynb` | DuckDuckGo wrapped in `deepagents.create_deep_agent`     | DuckDuckGo    | **DROP** (redundant)      |
| `yf_news_provider.ipynb`      | YahooFinanceNewsTool inside a 2-node LangGraph              | Yahoo Finance | **DROP** (redundant)      |

### Why those two get dropped

- **`yf_news_provider`** is a strict subset of the agentic news
  pattern — a 2-node LangGraph that wraps a single tool call. It
  exists to demonstrate `tools_condition`, but `rag_graph.py` already
  demonstrates that pattern with a real use case. Yahoo Finance news
  itself is covered by Finnhub (`market_news.py`) and DuckDuckGo
  (the news_aggregator port). Keeping it would mean three news
  providers doing the same job from three different sources.
- **`stock_news_deep_provider`** uses the `deepagents` framework
  instead of LangGraph. Same data source as `news_aggregator_chain`
  (DuckDuckGo), same goal (open-ended financial research), but with
  less structure (no planning phase, no relevance grading). Keeping
  both would mean maintaining two libraries to do one job. We pick
  LangGraph because the rest of the stack is already on it.

### Why `news_aggregator_chain` survives

It's structurally different from `market_news.py`:

- **`market_news.py`** is a **structured pipeline** — fetch curated
  category feeds from Finnhub, classify each article, aggregate.
  Good when you want "give me the macro picture for today."
- **`news_aggregator_chain`** is an **exploratory planner** —
  generate a research plan, fan out parallel DuckDuckGo searches,
  grade results for relevance, synthesize. Good when you want
  "research everything you can find about NVDA's antitrust
  situation."

These complement each other. The next step is to port the notebook
into `src/agent/news_aggregator.py` and add a `/research` route.
The plan:

```python
# src/agent/news_aggregator.py  (TODO)
def get_aggregator_graph(): ...        # cached singleton
async def run_research(topic: str) -> dict: ...

# src/agent/app.py
@app.post("/research")
@log_call(logger)
async def research_endpoint(body: ServiceRequest):
    req = unpack_request(body)
    topic = req.data.get("topic", "").strip()
    if not topic:
        return {"error": "empty topic"}
    from src.agent.news_aggregator import run_research
    return await run_research(topic)
```

The UI gets a sidebar button "Deep Research" that POSTs to
`/tools/research` with a topic input.

### Final agent count

5 agents under `src/`, down from 7 in the notebook deliverable:

1. **rag** — 10-K Q&A (Chroma + Ollama)
2. **market_news** — Finnhub categorized macro digest
3. **research** — DuckDuckGo exploratory planner *(pending port)*
4. **prices** — yfinance OHLCV + TA
5. **earnings** — Finnhub earnings calendar

`prices` and `earnings` are tool providers, not LLM agents — they
exist as building blocks the chat agent can call.

---

## 8. Configuration & secrets

All config lives in `.env` at the project root. Keys we read:

| Key                  | Purpose                                          | Default                  |
|----------------------|--------------------------------------------------|--------------------------|
| `TEXT_MODEL`         | Ollama text generation model                     | `llama3.2:latest`        |
| `EMBEDDING_MODEL`    | Ollama embedding model                           | `embeddinggemma:latest`  |
| `PERSISTENCE_PATH`   | Root of local persistence dir                    | `persistence`            |
| `VECTOR_DB_PATH`     | Subdir under persistence for Chroma              | `chroma`                 |
| `KB_PATH`            | Subdir under persistence for source PDFs         | `reference_files`        |
| `CHROMA_COLLECTION`  | Chroma collection name                           | `financial-collection`   |
| `FINNHUB_API_KEY`    | Finnhub API key (news + earnings)                | *(empty)*                |

Real API keys NEVER go in git. The `.env` in the repo today has
`FINNHUB_API_KEY=""` — fill it locally. Add `.env` to `.gitignore`
before the next commit if it isn't already.

Heavy LLM config (temperature, top-p, model overrides) is currently
hardcoded in `llm_loader.py` (`temperature=0.2`). When we need to
override per request, add a `params.model_overrides` dict to
`ServiceRequest` and read it inside the loader.

---

## 9. Dependencies

Two tiers, defined in `pyproject.toml`.

**Slim base** — installed by `pip install -e .`:

```
python-fasthtml, MonsterUI, fastapi, uvicorn,
aiohttp, pydantic, python-dotenv
```

This is enough to start both services and click through the UI.
Every agent route returns an error explaining what's missing.

**Full** — installed by `pip install -e ".[full]"`:

```
langchain, langchain-core, langchain-community,
langchain-ollama, langchain-chroma, langchain-unstructured,
langchain-text-splitters, langgraph, chromadb, ollama,
yfinance, finnhub-python, pandas, numpy, unstructured[pdf], pypdf
```

This is enough to run RAG, market news, prices, and earnings end to
end — assuming Ollama is running locally and `FINNHUB_API_KEY` is set.

**Optional system libs** (NOT installed by pip):

- **TA-Lib** — `price_history.py` attaches indicators only when
  `import talib` succeeds. Install via your OS package manager
  (`brew install ta-lib`, `apt install libta-lib0`, etc.) plus
  `pip install ta-lib`.
- **Poppler / Tesseract / libmagic** — needed by `unstructured` for
  PDF ingestion. `apt install poppler-utils tesseract-ocr libmagic1`
  on Debian/Ubuntu.

The full requirements.txt at the project root is the historical
notebook dep list (223 packages including torch, transformers,
opencv, google-cloud-vision). It is **not** what we install for the
service — keep it for reference but use `pyproject.toml`.

---

## 10. What's in the repo and what to ignore

| Path                             | Role                       | Touch?              |
|----------------------------------|----------------------------|---------------------|
| `src/`                           | shipping code              | yes                 |
| `main.py`, `pyproject.toml`      | launcher + deps            | yes                 |
| `ARCHITECTURE.md`, `README.md`   | docs                       | yes                 |
| `.env`                           | local config               | yes (locally only)  |
| `persistence/reference_files/`   | source PDFs                | yes (add new docs)  |
| `persistence/chroma/`            | Chroma vector store        | gitignore, runtime  |
| `logs/`                          | per-service log files      | gitignore, runtime  |
| `final-project-ipynbs/`          | original deliverable       | reference only      |
| `g(old)/`                        | pre-port modules           | reference only      |
| `requirements.txt`               | full notebook dep list     | reference only      |
| `financial_system.pdf`           | course material            | reference only      |

If you find Docker files, Streamlit code, or anything referencing
`docker-compose` in this repo, that's leftover from a teammate's
parallel branch — it is **not** part of the architecture and should
not be re-introduced.

---

## 11. Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"      # or just `pip install -e .` for the slim scaffold
python main.py
```

- UI: http://localhost:8010
- Agent: http://localhost:8011 (Swagger at `/docs`)

Ctrl+C in the launcher terminates both children. Each service can
also be run directly for debugging:

```bash
python src/agent/app.py    # uvicorn dev server on 8011
python src/ui/app.py       # FastHTML dev server on 8010 (auto-reload)
```

A typical first-run workflow:

1. `ollama serve` in another terminal.
2. `ollama pull llama3.2 && ollama pull embeddinggemma`.
3. `python main.py`.
4. Open http://localhost:8010, click **Continue**, click **Ingest
   PDFs** in the sidebar — this loads the AAPL 10-K into Chroma.
5. Type a question into the chat box. The first call is slow
   (loading the model); subsequent calls hit the cached singleton.

---

## 12. Open work

In rough order:

1. **Port `news_aggregator_chain.ipynb` to `src/agent/news_aggregator.py`**
   plus a `/research` route and a sidebar button. See §7.
2. **Wire chat history.** Today `/chat` is single-shot — `data.query`
   is the only field. Add `data.history: list[{"role", "content"}]`
   and thread it through `run_rag_query`.
3. **Move `AGENT_BASE_URL` into env.** Currently hardcoded in
   `src/ui/ui_utils.py`.
4. **Add a ticker selector to the prices/earnings sidebar buttons.**
   Right now they're hardcoded to `AAPL`.
5. **Auto-ingest on first boot** if Chroma is empty. Today the user
   has to click the **Ingest PDFs** button manually.
6. **Replace inline error strings with structured error codes** so
   the UI can render targeted help (e.g. "Ollama not running" vs
   "Finnhub key missing").

None of these are blocking — the scaffold runs as is.
