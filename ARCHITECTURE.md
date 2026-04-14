# Architecture

AAI-520 Group 7 — Multi-Agent Financial Advisor

This document is the canonical reference for how the project is built,
why the pieces are split the way they are, and how to extend it. The
end-user `README.md` covers install and run; this file covers
*decisions*. If a convention here conflicts with code, the code is
wrong — open a PR.

---

## 1. Overview

A two-service, hypermedia-driven financial research copilot. The
primary interaction is a single-button **AAPL stock assessment**: a
deterministic LangGraph fans out to three parallel data fetchers
(ticker-filtered company news, recent OHLCV, upcoming earnings),
fans in to an LLM that writes a targeted retrieval query, pulls
grounding passages from Apple's 2024 10-K via Chroma, and
synthesizes a structured assessment (thesis, outlook, bull/bear,
catalysts, risks). A right-hand sidebar exposes each data source as
a manual shortcut so users can drill into the raw signals without
running the full pipeline. The LLM stack is local (Ollama) so the
project runs without paid API keys. The vector store is local
(Chroma) so it survives restarts without external infra.

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
│   │   ├── chroma_store.py    # persistent Chroma + idempotent ingest
│   │   ├── pdf_loader.py      # PDF → langchain Document chunks
│   │   ├── rag_graph.py       # 10-K retrieval helper (retrieve_10k_context)
│   │   ├── stock_assessment.py# deterministic LangGraph — the main /assessment flow
│   │   ├── market_news.py     # Finnhub news (macro + per-ticker) + classifier graph
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

| Route          | Method | Body / Params                          | Returns                                       |
|----------------|--------|----------------------------------------|-----------------------------------------------|
| `/health`      | GET    | —                                      | liveness probe                                |
| `/assessment`  | POST   | `data.ticker`                          | structured `StockAssessment` (see §7)         |
| `/news`        | POST   | `data.category`, `params.limit`        | per-article classifier + aggregate stats     |
| `/prices`      | POST   | `data.symbol`, `params.window_days`    | OHLCV (+ TA if talib installed)               |
| `/earnings`    | POST   | `data.ticker`, `params.lookahead_days` | Finnhub earnings calendar                     |
| `/ingest`      | POST   | —                                      | `{new, skipped, total, files}` — idempotent  |

Every route returns `{"error": "..."}` on failure, never an HTTP 5xx.
The UI renders the error inline.

`/ingest` is safe to call repeatedly — chunks are keyed by a
deterministic SHA-256 of `source || content`, so re-ingesting the
same PDF skips everything already present and reports
`new: 0, skipped: N` instead of writing duplicate embeddings under
fresh UUIDs.

---

## 5. UI service routes

| Route             | Method | Triggers                                                 |
|-------------------|--------|----------------------------------------------------------|
| `/`               | GET    | launcher screen                                          |
| `/chat`           | GET    | assessment screen + sidebar; `?tour=1` mounts the tutorial modal |
| `/assessment`     | POST   | run the stock assessment graph → render the card        |
| `/tools/news`     | GET    | render market news card (macro feed)                     |
| `/tools/prices`   | GET    | render prices card                                       |
| `/tools/earnings` | GET    | render earnings card                                     |
| `/tools/ingest`   | POST   | render ingest result                                     |

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

## 7. The stock assessment graph (main flow)

The chat box does *not* accept a free-form question. User input is
irrelevant — the main interaction is a single button ("Generate AAPL
Assessment") that triggers a **deterministic multi-node LangGraph**
defined in `src/agent/stock_assessment.py`. We chose deterministic
over agentic/tool-calling because llama3.2 (our local model) is weak
at tool routing, and a fixed pipeline is easier to demo, easier to
grade, and lets every node use a dedicated prompt rather than one
generic supervisor prompt.

### Graph shape

```
               ┌─ fetch_news     ──┐
               │                   │
START ──▶ ────┼─ fetch_prices   ──┼──▶ build_rag_query ──▶ rag_context ──▶ synthesize ──▶ END
               │                   │
               └─ fetch_earnings ──┘
```

- **Three parallel fetch nodes** fan out from `START`. LangGraph
  runs them concurrently because they all write to different keys
  on the `AssessmentState` TypedDict (`news`, `prices`, `earnings`).
- **`build_rag_query`** is an LLM step (`llm.invoke`) that reads all
  three fetch outputs and writes ONE targeted retrieval question
  (<= 25 words) for the 10-K knowledge base. The prompt is
  aggressively ticker-anchored — it repeats the ticker in the system
  message, the user message, and an example. A safety net rejects
  any generated query that doesn't contain the ticker substring and
  falls back to `"What does {ticker}'s 10-K identify as its primary
  near-term risks and growth drivers?"`.
- **`rag_context`** is **pure retrieval** — calls
  `retrieve_10k_context` (thin wrapper around
  `Chroma.similarity_search`) and stuffs the top-5 chunks into state
  as a single annotated string. No LLM synthesis at this step; the
  chunks are raw inputs for the next node.
- **`synthesize`** is an LLM with `with_structured_output(StockAssessment)`.
  The Pydantic model locks the output shape (thesis, outlook badge,
  bull case, bear case, catalysts, risks). The prompt carries strict
  anti-hallucination rules: every bullet must cite a specific input
  signal, never attribute events to the wrong company, and return a
  single "Insufficient data in current signals" bullet when a section
  has no supporting evidence.

### Two different news sources, on purpose

The **sidebar** Market News tool and the **assessment graph** use
different Finnhub endpoints, and this is deliberate:

| Surface                       | Endpoint                        | Scope                      | Downstream processing                                     |
|-------------------------------|---------------------------------|----------------------------|-----------------------------------------------------------|
| Sidebar `/tools/news`         | `client.general_news(category)` | Macro feed (general/forex/…) | Per-article sentiment/category/bullets LangGraph         |
| Assessment `fetch_news` node  | `client.company_news(symbol)`   | Ticker-scoped, last 7 days  | Ticker-substring filter (via `_TICKER_ALIASES`), no LLM  |

Keeping both gives a complementary picture: the assessment is
anchored on Apple-specific news so the synthesizer never drifts,
while the sidebar shows the broader market context so the user can
sanity-check what's happening in the world around the stock. An
earlier iteration used the macro feed inside the assessment and the
downstream LLM immediately hijacked itself onto an unrelated
Lucid/Uber headline — the ticker-scoped endpoint plus the alias
filter is what keeps the grounding honest.

### 10-K context is frozen at 2024

The only PDF loaded into Chroma today is Apple's 2024 10-K filing.
The assessment card carries a footer disclaimer making this explicit,
and the synthesize prompt is aware that 10-K passages are historical
context while price/news/earnings signals are live. When a new 10-K
ships, re-running `/ingest` is safe — the content-hash chunk IDs
mean the old chunks will be deduped and only the new ones get
embedded. Swapping *versions* of the same filing (where the chunks
genuinely differ) will write new embeddings alongside the old ones;
if that becomes a problem, add a `source`-based purge before ingest.

### Agent inventory: where we landed

The original notebook deliverable had **seven** agents/workflows.
Four of them were news-oriented and overlapped heavily. The final
shipped inventory is 5 (one orchestrator + four building blocks):

| Component                      | Role                                                           | Status          |
|--------------------------------|----------------------------------------------------------------|-----------------|
| `stock_assessment.py`          | Orchestrator — the deterministic 6-node graph above            | **Shipped**     |
| `rag_graph.py`                 | Retrieval helper (`retrieve_10k_context`) used by assessment   | **Shipped**     |
| `market_news.py`               | Macro classifier graph (sidebar) + `fetch_company_news`        | **Shipped**     |
| `price_history.py`             | yfinance OHLCV + optional TA-Lib                               | **Shipped**     |
| `earnings_calendar.py`         | Finnhub earnings calendar                                      | **Shipped**     |
| `news_aggregator.py`           | DuckDuckGo exploratory planner from `news_aggregator_chain.ipynb` | *Pending port* |
| `yf_news_provider.ipynb`       | YahooFinanceNewsTool 2-node graph                              | **Dropped**     |
| `stock_news_deep_provider.ipynb` | `deepagents.create_deep_agent` wrapper                       | **Dropped**     |

Why the two drops: `yf_news_provider` duplicated Finnhub's coverage
with a less structured pattern, and `stock_news_deep_provider` used
the `deepagents` framework instead of LangGraph — keeping it would
have meant maintaining two agent libraries to do one job. LangGraph
wins because the rest of the stack is already on it.

`prices` and `earnings` are still tool providers (not LLM agents) —
building blocks the orchestrator calls, and the sidebar exposes
directly.

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
yfinance, finnhub-python, pandas, numpy, unstructured[pdf], pypdf,
TA-Lib
```

This is enough to run the assessment graph, market news, prices,
and earnings end to end — assuming Ollama is running locally and
`FINNHUB_API_KEY` is set. `TA-Lib` ships pre-built wheels (0.6.x+)
that bundle the underlying C library, so no separate system package
is required on Linux/macOS/Windows for the Python versions the
wheels support.

**Optional system libs** (NOT installed by pip):

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
4. Open http://localhost:8010, click **Get Started** — the tutorial
   modal walks through what the app does.
5. Click **Ingest PDFs** in the right sidebar to load Apple's 2024
   10-K into Chroma (idempotent — safe to re-run).
6. Click **Generate AAPL Assessment**. The first run is slow (Ollama
   cold start + 6-node graph + two LLM calls) but subsequent runs
   hit the cached model and compiled graph.

---

## 12. Open work

In rough order:

1. **Port `news_aggregator_chain.ipynb` to `src/agent/news_aggregator.py`**
   plus a `/research` route and a sidebar button. See §7.
2. **Move `AGENT_BASE_URL` into env.** Currently hardcoded in
   `src/ui/ui_utils.py`.
3. **Add a ticker selector** so the assessment button (and the
   prices/earnings sidebar shortcuts) are no longer hardcoded to
   `AAPL`. The graph is already ticker-generic — `_TICKER_ALIASES`
   in `stock_assessment.py` has entries for several large-caps.
4. **Auto-ingest on first boot** if Chroma is empty. Today the user
   has to click the **Ingest PDFs** button manually.
5. **Replace inline error strings with structured error codes** so
   the UI can render targeted help (e.g. "Ollama not running" vs
   "Finnhub key missing").
6. **Strip leading bullet markers** (`•`, `*`, `-`) in the assessment
   card's bullet rendering. llama3.2 occasionally prefixes its own
   markers inside a list item, and we already wrap in `<ul><li>`.
7. **Onboarding: cookie/localStorage for the tour modal.** Today the
   modal is gated by the launcher sending `?tour=1`. A returning
   visitor arriving directly at `/chat` sees no tour; a reloader
   arriving from the launcher sees it every time. Both are fine for
   the demo but a small JS (`localStorage.getItem('tour_seen')`)
   would make it auto-dismiss after the first visit.

None of these are blocking — the scaffold runs as is.
