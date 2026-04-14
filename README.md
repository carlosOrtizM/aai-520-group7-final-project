<div align="center">
<img align="center" width="30%" alt="image" src="https://www.sandiego.edu/assets/global/images/logos/logo-usd.png">
</div>

# Multi-Agent Financial Advisor

![](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![](https://img.shields.io/badge/MSAAI-NLP-blue?style=for-the-badge)
![](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)

aai-520-group7-final-project

A two-service financial research copilot. The main interaction is a
single-button **AAPL stock assessment**: a deterministic LangGraph
fans out to three parallel data fetchers (ticker-filtered company
news, recent OHLCV with TA indicators, upcoming earnings), fans in
to an LLM that writes a targeted 10-K retrieval query, pulls
grounding passages from Apple's 2024 10-K via Chroma, and synthesizes
a structured view (thesis, outlook, bull case, bear case, catalysts,
risks). A right-hand sidebar exposes each data source as a manual
shortcut so you can drill into the raw signals without running the
full pipeline.

The UI is hypermedia-driven (FastHTML + htmx, no JS framework); the
agent is a FastAPI service backed by local LLMs (Ollama) and a local
vector store (Chroma). For the full design rationale — service split,
contracts, the deterministic-vs-agentic decision, and the agent
consolidation plan — read [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Table of Contents
- [Overview](#overview)
- [Repo layout](#repo-layout)
- [Run it yourself](#run-it-yourself)
- [Agents](#agents)
- [Contributors](#contributors)
- [License](#license)

## Overview

The project started life as seven Jupyter notebooks demonstrating
LangChain / LangGraph patterns over financial data. We have since
re-architected it into a deployable two-service app under `src/`,
following the same pattern used by the `covered_caller` capstone
prototype. The notebooks remain in `final-project-ipynbs/` as the
original course deliverable; they are not imported at runtime.

Two services, two ports:

| Service | Stack                | Port  | Role                                                                 |
|---------|----------------------|-------|----------------------------------------------------------------------|
| UI      | FastHTML + MonsterUI | 8010  | Launcher, assessment screen, sidebar tools, htmx swaps, tutorial modal |
| Agent   | FastAPI + LangGraph  | 8011  | Stock assessment graph, news, prices, earnings, ingestion            |

They communicate over `aiohttp` POSTs using a shared `ServiceRequest`
Pydantic model. No Docker. No database. No Streamlit. No Gradio.

## Repo layout

```
agent-advisor/
├── main.py                    # launcher — spawns both services
├── pyproject.toml             # slim base deps + [full] extra
├── ARCHITECTURE.md            # design decisions, contracts, conventions
├── README.md                  # this file
├── .env                       # local config + API keys (NOT committed)
│
├── src/
│   ├── utils.py               # ServiceRequest, logger, log_call
│   ├── agent/                 # FastAPI service — :8011
│   │   ├── app.py
│   │   ├── llm_loader.py      # cached ChatOllama
│   │   ├── chroma_store.py    # persistent Chroma + idempotent ingest
│   │   ├── pdf_loader.py
│   │   ├── rag_graph.py       # 10-K retrieval helper
│   │   ├── stock_assessment.py# deterministic /assessment LangGraph (main flow)
│   │   ├── market_news.py     # Finnhub macro + company_news + classifier graph
│   │   ├── price_history.py   # yfinance + TA-Lib indicators
│   │   └── earnings_calendar.py
│   └── ui/                    # FastHTML service — :8010
│       ├── app.py
│       ├── ui_components.py   # assessment card, tutorial modal, loading toasts
│       ├── ui_handler.py
│       └── ui_utils.py
│
├── persistence/               # local state
│   ├── reference_files/       # source PDFs (AAPL 10-K, etc.)
│   ├── chroma/                # vector store (gitignored, runtime)
│   └── file_outputs/
│
├── logs/                      # per-service logs (auto-rotated daily)
│
├── final-project-ipynbs/      # original notebook deliverable (reference)
└── g(old)/                    # archived pre-port modules (reference)
```

## Run it yourself

### Prerequisites

- **Python 3.11+**
- **Ollama** — local LLM host. Install from <https://ollama.com/download>,
  then pull the models we use:
  ```bash
  ollama pull llama3.2
  ollama pull embeddinggemma
  ollama serve   # in its own terminal
  ```
- **Finnhub API key** (free tier is fine) — set `FINNHUB_API_KEY` in
  `.env`. Required for `/news`, `/earnings`, and the news-fetching
  step of `/assessment`. Prices and RAG work without it.
- **TA-Lib** — pulled in by `[full]` as the `TA-Lib` pip package,
  which ships pre-built wheels bundling the C library. No separate
  system package needed on Linux/macOS/Windows for supported Python
  versions. Indicators (MA, EMA, RSI, ADX, ATR, OBV) appear on both
  the sidebar prices card and the assessment graph's price signals.
- **Optional system libs for PDF ingestion** — `unstructured` needs
  `poppler`, `tesseract`, and `libmagic` to parse the 10-K:
  - **Debian / Ubuntu:** `sudo apt install poppler-utils tesseract-ocr libmagic1`
  - **macOS** (via [Homebrew](https://brew.sh/)): `brew install poppler tesseract libmagic`
  - **Apple Silicon note:** make sure `brew` is on your `PATH` (the
    installer prints the exact `eval` line). Ollama, Python 3.11+,
    and the `TA-Lib` wheel all ship arm64 builds, so the full stack
    runs natively on M1/M2/M3 — no Rosetta needed.

### Install

```bash
git clone <repo>
cd aai-520-group7-final-project

python -m venv .venv
source .venv/bin/activate

# Slim scaffold — both services start, agent routes return errors
# until you install [full]. Useful for UI-only iteration.
pip install -e .

# Full stack — RAG, news, prices, earnings all functional.
pip install -e ".[full]"
```

### Run

```bash
python main.py
```

- UI:    http://localhost:8010
- Agent: http://localhost:8011 (Swagger docs at `/docs`)

Ctrl+C terminates both services. You can also run each one directly:

```bash
python src/agent/app.py    # uvicorn dev server, port 8011
python src/ui/app.py       # FastHTML dev server, port 8010
```

### First-run flow

1. Start Ollama (`ollama serve`).
2. `python main.py`.
3. Open http://localhost:8010, click **Get Started** — a first-run
   tutorial modal walks through what the app does (main flow,
   sidebar tools, and what's running under the hood).
4. Click **Ingest PDFs** in the right sidebar to load Apple's 2024
   10-K from `persistence/reference_files/` into Chroma. This is
   idempotent — re-pressing the button reports "already up to date"
   instead of writing duplicate embeddings.
5. Click **Generate AAPL Assessment**. The first run takes ~2 minutes
   (Ollama cold start + the 6-node graph + two LLM calls) and
   returns a structured card: thesis, bullish/neutral/bearish
   outlook, bull and bear case bullets, catalysts, and risks —
   each grounded in live signals and the 10-K.
6. Exercise the sidebar shortcuts any time:
   - **Market News** — macro feed (broader than Apple; complements
     the assessment rather than duplicating it).
   - **AAPL Prices** — last 60 trading days of OHLCV + TA indicators.
   - **AAPL Earnings** — upcoming earnings calendar.

## Agents

One orchestrator (the deterministic assessment graph) plus four
building-block tool providers, down from 7 in the original notebook
deliverable. The two dropped notebooks (`yf_news_provider`,
`stock_news_deep_provider`) were redundant with the news pipeline
we kept — see [`ARCHITECTURE.md`](ARCHITECTURE.md) §7 for the full
inventory, the deterministic-vs-agentic decision, and the news
source split (sidebar shows macro headlines via `general_news`;
assessment uses ticker-filtered `company_news`).

| Component           | Module                            | Role                                                     | Status    |
|---------------------|-----------------------------------|----------------------------------------------------------|-----------|
| Stock assessment    | `src/agent/stock_assessment.py`   | Orchestrator — 6-node LangGraph, the main `/assessment` flow | shipped   |
| 10-K retrieval      | `src/agent/rag_graph.py`          | `retrieve_10k_context` — pure Chroma lookup helper       | shipped   |
| Market news         | `src/agent/market_news.py`        | Macro classifier graph + `fetch_company_news`            | shipped   |
| Price history       | `src/agent/price_history.py`      | yfinance OHLCV + TA-Lib indicators                       | shipped   |
| Earnings calendar   | `src/agent/earnings_calendar.py`  | Finnhub earnings calendar                                | shipped   |
| Deep research       | `src/agent/news_aggregator.py`    | DuckDuckGo exploratory planner                           | pending   |

## Contributors
<table>
  <tr>
    <td>
        <a href="https://github.com/carlosOrtizM">
          <img src="https://github.com/carlosOrtizM.png" width="100" height="100" alt="Carlos Ortiz "/><br />
          <sub><b>Carlos Ortiz</b></sub>
        </a>
      </td>
      <td>
        <a href="https://github.com/aditithakur-569">
          <img src="https://github.com/aditithakur-569.png" width="100" height="100" alt="Adhiti Jha "/><br />
          <sub><b>Adhiti Jha</b></sub>
        </a>
      </td>
  </tr>
</table>

## License

MIT License

Copyright (c) [2025]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
