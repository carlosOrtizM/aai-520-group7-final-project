"""UI -> agent bridge.

Each handler builds a ServiceRequest, opens a short-lived aiohttp
session, posts to the agent service, and returns the raw dict for the
@rt to render. Errors are caught here and surfaced as ``{"error": ...}``
so route handlers can render a uniform error card.
"""

import aiohttp

from src.ui.ui_utils import pack_request, pack_request_with_params, send_to_agent

# aiohttp's default total timeout is 5 minutes. The assessment graph
# finishes in ~2-3 min on a warm run, but an Ollama cold start (plus
# the classifier LLM's first load on the dedicated client) can push
# the first call of a session past 300s and the default timeout fires
# with an empty-string TimeoutError. 15 min is a generous cap that
# still catches a genuinely hung agent.
_ASSESSMENT_TIMEOUT = aiohttp.ClientTimeout(total=900)
_INGEST_TIMEOUT = aiohttp.ClientTimeout(total=600)


async def handle_assessment(ticker: str = "AAPL") -> dict:
    try:
        req = pack_request(ticker=ticker)
        async with aiohttp.ClientSession(timeout=_ASSESSMENT_TIMEOUT) as session:
            return await send_to_agent(session, req, "/assessment")
    except Exception as e:
        return {"error": f"assessment call failed: {e}"}


async def handle_news(category: str = "general", limit: int = 6) -> dict:
    try:
        req = pack_request_with_params({"category": category}, {"limit": limit})
        async with aiohttp.ClientSession() as session:
            return await send_to_agent(session, req, "/news")
    except Exception as e:
        return {"error": f"news call failed: {e}"}


async def handle_prices(symbol: str = "AAPL", window_days: int = 120) -> dict:
    try:
        req = pack_request_with_params(
            {"symbol": symbol}, {"window_days": window_days}
        )
        async with aiohttp.ClientSession() as session:
            return await send_to_agent(session, req, "/prices")
    except Exception as e:
        return {"error": f"prices call failed: {e}"}


async def handle_earnings(ticker: str = "AAPL", lookahead_days: int = 120) -> dict:
    try:
        req = pack_request_with_params(
            {"ticker": ticker}, {"lookahead_days": lookahead_days}
        )
        async with aiohttp.ClientSession() as session:
            return await send_to_agent(session, req, "/earnings")
    except Exception as e:
        return {"error": f"earnings call failed: {e}"}


async def handle_ingest() -> dict:
    try:
        req = pack_request()
        async with aiohttp.ClientSession(timeout=_INGEST_TIMEOUT) as session:
            return await send_to_agent(session, req, "/ingest")
    except Exception as e:
        return {"error": f"ingest call failed: {e}"}
