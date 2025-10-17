# import necessary libraries
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv
import os
import finnhub

load_dotenv()

class EarningsCalendarProvider:
    """
    Earnings date lookup with sensible fallbacks.
    Free Tier: 1 month of historical earnings and new updates...

    Order of operations:
      Try an optional user-supplied provider function (if given).

    A "provider function" should be:  (ticker: str, now_utc: datetime, lookahead_days: int) -> Iterable[datetime]
    It returns one or more candidate datetimes (past or future). We'll pick the next upcoming one.
    """

    def __init__(
            self,
            api_key: str,
            ticker: str,
            lookahead_days: int = 120,
            prefer_window: bool = True,
    ):
        self.client = finnhub.Client(api_key=api_key)
        self.lookahead_days = int(lookahead_days)
        self.ticker = ticker
        self.prefer_window = prefer_window  # prefer a date within lookahead window if multiple upcoming exist

    # ---------- public API ----------
    def future_earnings(self) -> Any | None:
        try:
            now = datetime.now(timezone.utc)
            window_end = now + timedelta(days=self.lookahead_days)

            # user provider
            dt = self.client.earnings_calendar(_from=now, to=window_end, symbol=self.ticker, international=False)
            if dt:
                return dt
        except Exception as e:
            print("Error fetching next_earnings error.", repr(e))

ct = EarningsCalendarProvider(ticker="AAPL", api_key=os.getenv("FINNHUB_API_KEY"))
calendar = ct.future_earnings()
print(f"Future earnings calendar: {calendar}")
print(calendar)