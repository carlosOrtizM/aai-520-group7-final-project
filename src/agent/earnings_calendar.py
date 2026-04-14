"""Earnings calendar lookup via Finnhub.

Ported from g(old)/session_init/earnings_calendar_provider.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from src.config import FINNHUB_API_KEY


def fetch_future_earnings(ticker: str, lookahead_days: int = 120) -> dict[str, Any]:
    """Fetch upcoming earnings for a ticker over the next ``lookahead_days``."""
    import finnhub

    client = finnhub.Client(api_key=FINNHUB_API_KEY)
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=lookahead_days)

    payload = client.earnings_calendar(
        _from=now.strftime("%Y-%m-%d"),
        to=window_end.strftime("%Y-%m-%d"),
        symbol=ticker,
        international=False,
    )
    return {
        "ticker": ticker,
        "lookahead_days": lookahead_days,
        "calendar": payload or {},
    }
