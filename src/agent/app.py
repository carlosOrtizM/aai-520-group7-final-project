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
from src.utils import ServiceRequest, create_logger, log_call

logger = create_logger("agent")

app = FastAPI(title="Agent Advisor — Agent Service")


@app.get("/health")
async def health_endpoint():
    """Lightweight liveness probe — no deps required."""
    return {"status": "ok", "service": "agent", "port": 8011}


@app.post("/chat")
@log_call(logger)
async def chat_endpoint(body: ServiceRequest):
    """RAG chat — runs the langgraph RAG pipeline on a user query.

    Body shape:
        data = {"query": "..."}
        params = {}  # reserved (history limits, model overrides, etc.)
    """
    try:
        req = unpack_request(body)
        query = req.data.get("query", "").strip()
        if not query:
            return {"error": "empty query"}

        from src.agent.rag_graph import run_rag_query

        return await run_rag_query(query)
    except Exception as e:
        logger.error(f"Error on /chat: {e}")
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
            return {"ingested": 0, "note": "no PDFs found in KB path"}
        count = ingest_documents(docs)
        return {"ingested": count, "files": len(docs)}
    except Exception as e:
        logger.error(f"Error on /ingest: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
