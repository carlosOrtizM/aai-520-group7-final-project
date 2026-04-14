<div align="center">
<img align="center" width="30%" alt="image" src="https://www.sandiego.edu/assets/global/images/logos/logo-usd.png">
</div>

# Multi-Agent Financial Advisor

![](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![](https://img.shields.io/badge/MSAAI-NLP-blue?style=for-the-badge)
![](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)

aai-520-group7-final-project

A two-service financial research copilot. The UI is a hypermedia-driven
chat (FastHTML + htmx, no JS framework) and the agent is a FastAPI
service backed by local LLMs (Ollama) and a local vector store (Chroma).
For the full design rationale — service split, contracts, conventions,
and the agent consolidation plan — read [`ARCHITECTURE.md`](ARCHITECTURE.md).

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

| Service | Stack                | Port  | Role                                            |
|---------|----------------------|-------|-------------------------------------------------|
| UI      | FastHTML + MonsterUI | 8010  | Chat screen, sidebar tools, htmx swaps          |
| Agent   | FastAPI + LangGraph  | 8011  | RAG, news, prices, earnings, ingestion          |

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
│   │   ├── chroma_store.py    # persistent Chroma + ingest
│   │   ├── pdf_loader.py
│   │   ├── rag_graph.py       # 10-K Q&A
│   │   ├── market_news.py     # Finnhub + sentiment/category graph
│   │   ├── price_history.py   # yfinance + optional TA-Lib
│   │   └── earnings_calendar.py
│   └── ui/                    # FastHTML service — :8010
│       ├── app.py
│       ├── ui_components.py
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
  `.env`. Required for `/news` and `/earnings`. Other routes work
  without it.
- **Optional system libs:**
  - `poppler`, `tesseract`, `libmagic` — for PDF ingestion via the
    `unstructured` library. On Debian/Ubuntu:
    `sudo apt install poppler-utils tesseract-ocr libmagic1`.
  - `TA-Lib` — for technical indicators on `/prices`. Optional;
    `price_history.py` falls back to plain OHLCV if missing.

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
3. Open http://localhost:8010, click **Continue**.
4. In the chat screen sidebar, click **Ingest PDFs** to load the
   AAPL 10-K from `persistence/reference_files/` into Chroma.
5. Type a question into the chat box. The first call is slow
   (model warm-up); subsequent calls hit the cached LangGraph.
6. Try the **Market News**, **AAPL Prices**, **AAPL Earnings**
   sidebar buttons to exercise the tool routes.

## Agents

5 agents under `src/agent/`, down from 7 in the original notebook
deliverable. The two dropped notebooks (`yf_news_provider`,
`stock_news_deep_provider`) were redundant with the news pipeline
we kept — see [`ARCHITECTURE.md`](ARCHITECTURE.md) §7 for the full
inventory and rationale.

| Agent           | Module                          | Source         | Status        |
|-----------------|---------------------------------|----------------|---------------|
| RAG (10-K Q&A)  | `src/agent/rag_graph.py`        | local PDF      | ✅ ported      |
| Market news     | `src/agent/market_news.py`      | Finnhub        | ✅ ported      |
| Deep research   | `src/agent/news_aggregator.py`  | DuckDuckGo     | ⏳ pending     |
| Price history   | `src/agent/price_history.py`    | yfinance       | ✅ ported      |
| Earnings calendar | `src/agent/earnings_calendar.py` | Finnhub      | ✅ ported      |

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
