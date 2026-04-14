"""FastHTML UI service — port 8010.

Hypermedia-driven (no JS beyond htmx). Routes ingest user input,
delegate to ui_handler (which talks to the agent service over aiohttp),
and render components defined in ui_components. Errors are caught at
every entry point and rendered as inline cards.
"""

from fasthtml.common import *  # noqa: F401,F403
from monsterui.all import *  # noqa: F401,F403

from src.ui.ui_components import (
    USD_BRAND_CSS,
    bot_message,
    chat_exchange,
    chat_screen,
    earnings_card,
    error_card,
    ingest_card,
    launcher_screen,
    news_card,
    prices_card,
    user_message,
)
from src.ui.ui_handler import (
    handle_chat,
    handle_earnings,
    handle_ingest,
    handle_news,
    handle_prices,
)
from src.utils import create_logger, log_call

logger = create_logger("ui")

app, rt = fast_app(
    pico=False,
    hdrs=(
        *Theme.blue.headers(),
        USD_BRAND_CSS,
    ),
)


@rt("/")
@log_call(logger)
def get():
    try:
        return launcher_screen()
    except Exception as e:
        logger.error(f"Error rendering launcher: {e}")
        return Div(P("Something went wrong.", cls="uk-text-danger"))


@rt("/chat")
@log_call(logger)
def get():
    try:
        return chat_screen()
    except Exception as e:
        logger.error(f"Error rendering chat screen: {e}")
        return Div(P("Error loading chat.", cls="uk-text-danger"))


@rt("/send")
@log_call(logger)
async def post(query: str = ""):
    """Submit a chat message to the agent service and append both turns."""
    text = (query or "").strip()
    if not text:
        return Div()
    try:
        result = await handle_chat(text)
        if "error" in result:
            return Div(user_message(text), error_card(f"Agent: {result['error']}"))
        answer = result.get("answer", "(no answer)")
        return chat_exchange(text, answer)
    except Exception as e:
        logger.error(f"Error on /send: {e}")
        return Div(user_message(text), error_card("Agent request failed."))


@rt("/tools/news")
@log_call(logger)
async def get(category: str = "general"):
    try:
        payload = await handle_news(category=category, limit=6)
        return news_card(payload)
    except Exception as e:
        logger.error(f"Error on /tools/news: {e}")
        return error_card("News request failed.")


@rt("/tools/prices")
@log_call(logger)
async def get(symbol: str = "AAPL", window_days: int = 120):
    try:
        payload = await handle_prices(symbol=symbol, window_days=window_days)
        return prices_card(payload)
    except Exception as e:
        logger.error(f"Error on /tools/prices: {e}")
        return error_card("Prices request failed.")


@rt("/tools/earnings")
@log_call(logger)
async def get(ticker: str = "AAPL", lookahead_days: int = 120):
    try:
        payload = await handle_earnings(ticker=ticker, lookahead_days=lookahead_days)
        return earnings_card(payload)
    except Exception as e:
        logger.error(f"Error on /tools/earnings: {e}")
        return error_card("Earnings request failed.")


@rt("/tools/ingest")
@log_call(logger)
async def post():
    try:
        payload = await handle_ingest()
        return ingest_card(payload)
    except Exception as e:
        logger.error(f"Error on /tools/ingest: {e}")
        return error_card("Ingest request failed.")


if __name__ == "__main__":
    serve(port=8010)
