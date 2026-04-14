"""Price history + technical indicators.

Ported from g(old)/session_init/price_history_provider.py. talib is
optional — when missing we still return OHLCV without indicators so the
service stays useful on machines without the system library.
"""

from datetime import datetime, timedelta
from typing import Any


def fetch_price_history(symbol: str = "AAPL", window_days: int = 120) -> dict[str, Any]:
    """Download OHLCV history for ``symbol`` and (optionally) attach TA columns."""
    import yfinance as yf

    end_date = datetime.today()
    begin_date = end_date - timedelta(days=window_days)
    df = yf.download(
        symbol,
        start=begin_date,
        end=end_date,
        progress=False,
        multi_level_index=False,
    )
    if df is None or df.empty:
        return {"symbol": symbol, "rows": 0, "data": []}

    df = df.copy()
    if hasattr(df.index, "tz_localize"):
        try:
            df.index = df.index.tz_localize(None)
        except Exception:
            pass

    _try_attach_indicators(df)

    df = df.reset_index()
    if "Date" in df.columns:
        df["Date"] = df["Date"].astype(str)
    records = df.tail(60).to_dict(orient="records")
    return {
        "symbol": symbol,
        "window_days": window_days,
        "rows": len(records),
        "data": records,
        "indicators_available": "RSI" in df.columns,
    }


def _try_attach_indicators(df) -> None:
    """Attach a small set of TA-Lib indicators if the lib is available."""
    try:
        import talib
    except ImportError:
        return

    try:
        df["MA"] = talib.MA(df["Close"], timeperiod=10)
        df["EMA"] = talib.EMA(df["Close"], timeperiod=10)
        df["RSI"] = talib.RSI(df["Close"], timeperiod=14)
        df["ADX"] = talib.ADX(df["High"], df["Low"], df["Close"], timeperiod=10)
        df["ATR"] = talib.ATR(df["High"], df["Low"], df["Close"], timeperiod=14)
        df["OBV"] = talib.OBV(df["Close"], df["Volume"])
    except Exception:
        pass
