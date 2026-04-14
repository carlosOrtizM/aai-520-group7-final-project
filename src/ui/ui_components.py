"""FastHTML/MonsterUI components for the agent advisor UI.

Components only — no routing, no inter-service calls, no business
logic. The @rt handlers in app.py compose these into responses.
"""

from fasthtml.common import *  # noqa: F401,F403
from monsterui.all import *  # noqa: F401,F403


USD_BRAND_CSS = Style("""
    :root {
        --usd-founders: #003b70;
        --usd-immaculata: #0074c8;
        --usd-torero: #75bee9;
    }
    body { margin: 0; padding: 0; }
    .uk-container, .uk-section { max-width: 100% !important; width: 100% !important; }
    .chat-message-user {
        background: var(--usd-immaculata);
        color: white;
        padding: 10px 14px;
        border-radius: 14px 14px 2px 14px;
        margin: 8px 0;
        max-width: 70%;
        margin-left: auto;
    }
    .chat-message-bot {
        background: #f0f4f8;
        color: #1a1a1a;
        padding: 10px 14px;
        border-radius: 14px 14px 14px 2px;
        margin: 8px 0;
        max-width: 70%;
    }
    .tool-card {
        border: 1px solid #e0e7ef;
        border-radius: 10px;
        padding: 16px;
        margin: 10px 0;
        background: white;
    }
""")


def launcher_screen():
    """Minimalist landing page with a Continue button."""
    return Html(
        Head(
            Title("Agent Advisor"),
            USD_BRAND_CSS,
        ),
        Body(
            Div(
                H1("Agent Advisor", style="color: var(--usd-founders); margin-bottom: 8px;"),
                P("AAI-520 Group 7 — Financial Research Copilot",
                  style="color: #555; margin-bottom: 32px;"),
                A(
                    Button("Continue", cls=ButtonT.primary),
                    href="/chat",
                ),
                style=(
                    "display:flex; flex-direction:column; align-items:center; "
                    "justify-content:center; height:100vh;"
                ),
            ),
        ),
    )


def chat_screen():
    """Two-column chat layout — message thread + tools sidebar."""
    return Html(
        Head(
            Title("Agent Advisor — Chat"),
            USD_BRAND_CSS,
        ),
        Body(
            Div(
                _chat_main(),
                _tools_sidebar(),
                style="display:flex; height:100vh; gap:0;",
            ),
        ),
    )


def _chat_main():
    return Div(
        Div(
            H3("Chat", style="margin:0; color: var(--usd-founders);"),
            P("Ask about Apple's 10-K, market news, prices, or upcoming earnings.",
              style="color:#666; font-size:13px; margin:4px 0 0 0;"),
            style="padding: 16px 24px; border-bottom: 1px solid #e0e7ef;",
        ),
        Div(
            id="chat-thread",
            style=(
                "flex:1; overflow-y:auto; padding: 16px 24px; "
                "background: #fafbfc;"
            ),
        ),
        Form(
            Div(
                Input(
                    type="text",
                    name="query",
                    placeholder="Type your question...",
                    cls="uk-input",
                    style="flex:1;",
                    autofocus=True,
                ),
                Button("Send", cls=ButtonT.primary, type="submit"),
                style="display:flex; gap:8px;",
            ),
            hx_post="/send",
            hx_target="#chat-thread",
            hx_swap="beforeend",
            hx_on__after_request="this.reset()",
            style="padding: 16px 24px; border-top: 1px solid #e0e7ef; background:white;",
        ),
        style="flex:1; display:flex; flex-direction:column;",
    )


def _tools_sidebar():
    return Div(
        H4("Tools", style="margin:0 0 12px 0; color: var(--usd-founders);"),
        Div(
            Button(
                "Market News",
                cls=ButtonT.secondary,
                hx_get="/tools/news",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                style="width:100%; margin-bottom:8px;",
            ),
            Button(
                "AAPL Prices",
                cls=ButtonT.secondary,
                hx_get="/tools/prices?symbol=AAPL",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                style="width:100%; margin-bottom:8px;",
            ),
            Button(
                "AAPL Earnings",
                cls=ButtonT.secondary,
                hx_get="/tools/earnings?ticker=AAPL",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                style="width:100%; margin-bottom:8px;",
            ),
            Button(
                "Ingest PDFs",
                cls=ButtonT.secondary,
                hx_post="/tools/ingest",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                style="width:100%; margin-bottom:16px;",
            ),
        ),
        Div(id="tool-output"),
        style=(
            "width: 340px; padding: 24px; border-left: 1px solid #e0e7ef; "
            "background: white; overflow-y: auto;"
        ),
    )


def user_message(text: str):
    return Div(P(text, style="margin:0;"), cls="chat-message-user")


def bot_message(text: str):
    return Div(P(text, style="margin:0; white-space:pre-wrap;"), cls="chat-message-bot")


def chat_exchange(user_text: str, bot_text: str):
    """Append both the user's message and the bot reply in one swap."""
    return Div(user_message(user_text), bot_message(bot_text))


def error_card(message: str):
    return Div(
        P(message, style="color:#c62828; margin:0;"),
        cls="tool-card",
        style="border-color:#f5b8b8; background:#fff5f5;",
    )


def news_card(payload: dict):
    if "error" in payload:
        return error_card(f"News: {payload['error']}")
    analyses = payload.get("analyses", [])
    if not analyses:
        return Div(P("No news returned.", style="margin:0;"), cls="tool-card")
    items = [
        Div(
            P(Strong(a.get("headline", "(no headline)")), style="margin:0 0 4px 0;"),
            P(
                f"{a.get('label', '?')} | {a.get('sentiment', '?')}",
                style="margin:0; font-size:12px; color:#666;",
            ),
            P(a.get("bullets", ""), style="margin:6px 0 0 0; font-size:13px; white-space:pre-wrap;"),
            style="padding:8px 0; border-bottom:1px solid #eef2f7;",
        )
        for a in analyses
    ]
    return Div(
        H4(f"Market News — {payload.get('category', 'general')}", style="margin:0 0 8px 0;"),
        *items,
        cls="tool-card",
    )


def prices_card(payload: dict):
    if "error" in payload:
        return error_card(f"Prices: {payload['error']}")
    rows = payload.get("data", [])
    if not rows:
        return Div(P("No price data returned.", style="margin:0;"), cls="tool-card")
    last = rows[-1]
    close = last.get("Close")
    return Div(
        H4(f"{payload.get('symbol', '?')} — Price History", style="margin:0 0 8px 0;"),
        P(
            f"Last close: {close:.2f}" if isinstance(close, (int, float)) else f"Last close: {close}",
            style="margin:0;",
        ),
        P(
            f"{payload.get('rows', 0)} rows, indicators: "
            f"{'on' if payload.get('indicators_available') else 'off'}",
            style="margin:4px 0 0 0; font-size:12px; color:#666;",
        ),
        cls="tool-card",
    )


def earnings_card(payload: dict):
    if "error" in payload:
        return error_card(f"Earnings: {payload['error']}")
    cal = payload.get("calendar") or {}
    events = cal.get("earningsCalendar") or []
    if not events:
        return Div(
            H4(f"{payload.get('ticker', '?')} — Upcoming Earnings", style="margin:0 0 8px 0;"),
            P("No upcoming earnings within the lookahead window.", style="margin:0;"),
            cls="tool-card",
        )
    items = [
        Div(
            P(Strong(e.get("date", "?")), style="margin:0;"),
            P(
                f"EPS est: {e.get('epsEstimate', '?')}, hour: {e.get('hour', '?')}",
                style="margin:0; font-size:12px; color:#666;",
            ),
            style="padding:6px 0; border-bottom:1px solid #eef2f7;",
        )
        for e in events
    ]
    return Div(
        H4(f"{payload.get('ticker', '?')} — Upcoming Earnings", style="margin:0 0 8px 0;"),
        *items,
        cls="tool-card",
    )


def ingest_card(payload: dict):
    if "error" in payload:
        return error_card(f"Ingest: {payload['error']}")
    return Div(
        H4("Ingest", style="margin:0 0 8px 0;"),
        P(
            f"Files: {payload.get('files', 0)} | Chunks: {payload.get('ingested', 0)}",
            style="margin:0;",
        ),
        P(payload.get("note", ""), style="margin:4px 0 0 0; font-size:12px; color:#666;")
        if payload.get("note")
        else None,
        cls="tool-card",
    )
