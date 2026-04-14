"""FastAPI agent service — port 8011.

Twin of the FastHTML UI on :8010. Routes follow the same shape as the
covered_caller/inference service: every entry point wraps its work in
try/except, logs to a per-service logger, and returns a JSON dict (with
an ``error`` key on failure) so the UI can render gracefully.

Heavy LLM/RAG dependencies are imported lazily inside route bodies so
the service starts cleanly even when langchain/ollama are not yet
installed — a missing dep surfaces as a friendly error per request,
not a startup crash.
"""

from fastapi import FastAPI
import uvicorn

from src.agent.agent_utils import unpack_request, validate_ticker
from src.config import missing_required
from src.utils import ServiceRequest, create_logger, log_call

logger = create_logger("agent")

# Missing required config silently degrades routes (e.g. an empty
# FINNHUB_API_KEY makes /news and /earnings return empty payloads
# three minutes into an assessment run). Log one clear warning at
# boot so it surfaces in logs/agent_<date>.txt instead of as a
# head-scratch later.
_missing_config = missing_required()
if _missing_config:
    logger.warning(
        "Missing required config: %s — related routes will return "
        "empty payloads. Set these in .env (copy .env.example to "
        ".env and fill them in).",
        ", ".join(_missing_config),
    )

app = FastAPI(title="Agent Advisor — Agent Service")


@app.get("/health")
async def health_endpoint():
    """Lightweight liveness probe — no deps required."""
    return {"status": "ok", "service": "agent", "port": 8011}


@app.post("/assessment")
@log_call(logger)
async def assessment_endpoint(body: ServiceRequest):
    """Deterministic stock assessment — fan-out fetch → RAG → synthesize.

    Body shape:
        data = {"ticker": "AAPL"}
        params = {}  # reserved
    """
    try:
        req = unpack_request(body)
        ticker = req.data.get("ticker", "AAPL").upper()
        if not validate_ticker(ticker):
            return {"error": f"invalid ticker: {ticker}"}

        from src.agent.stock_assessment import run_stock_assessment

        return await run_stock_assessment(ticker)
    except Exception as e:
        logger.error(f"Error on /assessment: {e}")
        return {"error": str(e)}


@app.post("/news")
@log_call(logger)
async def news_endpoint(body: ServiceRequest):
    """Fetch + summarize market news for a Finnhub category."""
    try:
        req = unpack_request(body)
        category = req.data.get("category", "general")
        limit = int(req.params.get("limit", 6))

        from src.agent.market_news import summarize_market_news

        return await summarize_market_news(category=category, limit=limit)
    except Exception as e:
        logger.error(f"Error on /news: {e}")
        return {"error": str(e)}


@app.post("/prices")
@log_call(logger)
async def prices_endpoint(body: ServiceRequest):
    """Fetch OHLCV history (and TA indicators when talib is installed)."""
    try:
        req = unpack_request(body)
        symbol = req.data.get("symbol", "AAPL").upper()
        if not validate_ticker(symbol):
            return {"error": f"invalid ticker: {symbol}"}
        window_days = int(req.params.get("window_days", 120))

        from src.agent.price_history import fetch_price_history

        return fetch_price_history(symbol=symbol, window_days=window_days)
    except Exception as e:
        logger.error(f"Error on /prices: {e}")
        return {"error": str(e)}


@app.post("/earnings")
@log_call(logger)
async def earnings_endpoint(body: ServiceRequest):
    """Look up upcoming earnings for a ticker."""
    try:
        req = unpack_request(body)
        ticker = req.data.get("ticker", "AAPL").upper()
        if not validate_ticker(ticker):
            return {"error": f"invalid ticker: {ticker}"}
        lookahead = int(req.params.get("lookahead_days", 120))

        from src.agent.earnings_calendar import fetch_future_earnings

        return fetch_future_earnings(ticker=ticker, lookahead_days=lookahead)
    except Exception as e:
        logger.error(f"Error on /earnings: {e}")
        return {"error": str(e)}


@app.post("/ingest")
@log_call(logger)
async def ingest_endpoint(body: ServiceRequest):
    """One-shot PDF -> Chroma ingestion using the configured KB path."""
    try:
        from src.agent.chroma_store import ingest_documents
        from src.agent.pdf_loader import directory_iterator

        docs = directory_iterator()
        if not docs:
            return {
                "new": 0,
                "skipped": 0,
                "total": 0,
                "files": 0,
                "note": "no PDFs found in KB path",
            }
        stats = ingest_documents(docs)
        stats["files"] = len(docs)
        return stats
    except Exception as e:
        logger.error(f"Error on /ingest: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
