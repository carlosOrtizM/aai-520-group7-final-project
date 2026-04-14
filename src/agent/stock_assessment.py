"""Deterministic stock assessment graph.

Fan-out from START into three parallel fetch nodes (news, prices,
earnings), then fan-in to ``build_rag_query`` (LLM writes a targeted
retrieval question from the live data), then ``rag_context`` (pure
retrieval from the 10-K vector store), then ``synthesize`` (LLM with
structured output produces the final assessment).

    START ──┬─▶ fetch_news     ──┐
            ├─▶ fetch_prices   ──┼─▶ build_rag_query ─▶ rag_context ─▶ synthesize ─▶ END
            └─▶ fetch_earnings ──┘

Unlike the sidebar news tool (which runs the per-article
sentiment/category/synthesizer graph), this flow uses the RAW Finnhub
news fetch for speed — the ``build_rag_query`` node is the one that
reasons over the headlines.
"""

from typing import Any, Literal, TypedDict

_GRAPH_SINGLETON = None

# Symbol → company-name aliases for headline relevance filtering.
# Finnhub's company_news endpoint bundles adjacent-ticker stories
# (e.g. an Amazon/Globalstar headline surfaces in the AAPL feed),
# which causes llama3.2 to confuse entities downstream. We drop any
# headline that doesn't explicitly mention the ticker or its known
# aliases before passing news into the rest of the graph.
_TICKER_ALIASES: dict[str, tuple[str, ...]] = {
    "AAPL": ("aapl", "apple"),
    "MSFT": ("msft", "microsoft"),
    "GOOGL": ("googl", "google", "alphabet"),
    "GOOG": ("goog", "google", "alphabet"),
    "AMZN": ("amzn", "amazon"),
    "META": ("meta", "facebook"),
    "NVDA": ("nvda", "nvidia"),
    "TSLA": ("tsla", "tesla"),
}


def _headline_mentions_ticker(article: dict, ticker: str) -> bool:
    """True if the article headline/summary explicitly names the target ticker."""
    needles = set(_TICKER_ALIASES.get(ticker.upper(), (ticker.lower(),)))
    needles.add(ticker.lower())
    text = (article.get("headline", "") + " " + article.get("summary", "")).lower()
    return any(needle in text for needle in needles)


class AssessmentState(TypedDict, total=False):
    ticker: str
    news: list[dict]
    prices: dict
    earnings: dict
    rag_query: str
    rag_context: str
    assessment: dict


# ---------------------------------------------------------------------------
# Fetch nodes (fan-out)
# ---------------------------------------------------------------------------


def _fetch_news_node(state: AssessmentState) -> dict:
    """Pull ticker-specific headlines from Finnhub over the last week.

    First smoke run used the macro ``general_news`` feed, which made the
    downstream query builder drift onto unrelated names (a Lucid/Uber
    headline hijacked the whole assessment). Swapped to ``company_news``
    scoped to the requested ticker so every headline is about the stock
    being assessed.
    """
    try:
        # Old (macro feed — caused query-builder drift, kept as reference):
        # from src.agent.market_news import fetch_news
        # raw = fetch_news("general")[:6]
        from src.agent.market_news import fetch_company_news

        ticker = state["ticker"]
        raw = fetch_company_news(ticker, lookback_days=7)
        relevant = [a for a in raw if _headline_mentions_ticker(a, ticker)][:6]
        return {
            "news": [
                {
                    "headline": a.get("headline", ""),
                    "summary": a.get("summary", ""),
                }
                for a in relevant
            ]
        }
    except Exception:
        return {"news": []}


def _fetch_prices_node(state: AssessmentState) -> dict:
    """Pull last 60 sessions of OHLCV from yfinance."""
    try:
        from src.agent.price_history import fetch_price_history

        prices = fetch_price_history(symbol=state["ticker"], window_days=90)
        return {"prices": prices}
    except Exception:
        return {"prices": {"symbol": state["ticker"], "rows": 0, "data": []}}


def _fetch_earnings_node(state: AssessmentState) -> dict:
    """Pull upcoming earnings calendar from Finnhub."""
    try:
        from src.agent.earnings_calendar import fetch_future_earnings

        earnings = fetch_future_earnings(
            ticker=state["ticker"], lookahead_days=120
        )
        return {"earnings": earnings}
    except Exception:
        return {"earnings": {"ticker": state["ticker"], "calendar": {}}}


# ---------------------------------------------------------------------------
# Query builder → retrieval → synthesis (sequential tail)
# ---------------------------------------------------------------------------


def _summarize_prices(prices: dict) -> str:
    data = prices.get("data", [])
    if not data:
        return "(no price data)"
    closes = [r.get("Close") for r in data if r.get("Close") is not None]
    if not closes:
        return "(no close prices)"
    last = closes[-1]
    first = closes[0]
    pct = ((last - first) / first * 100) if first else 0.0
    return f"{len(closes)} sessions: ${first:,.2f} → ${last:,.2f} ({pct:+.1f}%)"


def _summarize_earnings(earnings: dict) -> str:
    events = (earnings.get("calendar") or {}).get("earningsCalendar") or []
    if not events:
        return "(no upcoming earnings in window)"
    nxt = events[0]
    return (
        f"Next earnings {nxt.get('date', '?')} "
        f"(EPS est {nxt.get('epsEstimate', 'N/A')}, "
        f"hour {nxt.get('hour', '?')})"
    )


def _summarize_headlines(news: list[dict]) -> str:
    if not news:
        return "(no headlines)"
    return "\n".join(f"- {n.get('headline', '').strip()}" for n in news if n.get("headline"))


def _build_rag_query_node(state: AssessmentState) -> dict:
    """LLM reads news+prices+earnings and formulates a 10-K retrieval question.

    The prompt is aggressively ticker-anchored because llama3.2 is small
    enough to drift onto other company names that appear in headlines
    (the first smoke run hijacked itself onto a Lucid/Uber headline from
    the macro feed). The system message, the user message, and an example
    all repeat the target ticker to keep the generation on-rails.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    from src.agent.llm_loader import get_llm_client

    llm = get_llm_client()
    ticker = state["ticker"]

    headlines = _summarize_headlines(state.get("news", []))
    price_line = _summarize_prices(state.get("prices", {}))
    earnings_line = _summarize_earnings(state.get("earnings", {}))

    system_msg = (
        f"You generate a single 10-K retrieval query about {ticker}. "
        f"The query MUST be about {ticker} and only {ticker}. "
        f"Never redirect the query to other companies mentioned in the "
        f"input headlines — they are context signals, not the subject."
    )

    prompt = (
        f"TICKER: {ticker}\n\n"
        f"RECENT {ticker}-SPECIFIC HEADLINES:\n{headlines}\n\n"
        f"PRICE ACTION: {price_line}\n"
        f"UPCOMING EARNINGS: {earnings_line}\n\n"
        f"TASK: Write ONE focused question (<= 25 words) to ask {ticker}'s "
        f"10-K knowledge base. The question must:\n"
        f"  1. Be about {ticker} (never another company).\n"
        f"  2. Reference a specific signal from the headlines, price action, "
        f"or upcoming earnings above.\n"
        f"  3. Help contextualize a near-term investment view.\n\n"
        f"FORMAT: return ONLY the question — no preamble, no quotes, no "
        f"explanation.\n\n"
        f"EXAMPLE: How does {ticker}'s 10-K describe its exposure to "
        f"<specific risk or driver drawn from the signals above>?"
    )

    response = llm.invoke(
        [
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt),
        ]
    )

    query = (response.content or "").strip().strip('"').strip("'")
    if not query or ticker.upper() not in query.upper():
        query = (
            f"What does {ticker}'s 10-K identify as its primary near-term "
            f"risks and growth drivers?"
        )
    return {"rag_query": query}


def _rag_context_node(state: AssessmentState) -> dict:
    """Pure retrieval — top-k 10-K chunks for the built query."""
    from src.agent.rag_graph import retrieve_10k_context

    context = retrieve_10k_context(state.get("rag_query", ""), k=5)
    return {"rag_context": context}


def _synthesize_node(state: AssessmentState) -> dict:
    """LLM with structured output produces the final assessment."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from pydantic import BaseModel, Field

    from src.agent.llm_loader import get_llm_client

    class StockAssessment(BaseModel):
        thesis: str = Field(description="One-sentence investment thesis.")
        outlook: Literal["bullish", "neutral", "bearish"] = Field(
            description="Near-term outlook tag."
        )
        bull_case: list[str] = Field(
            description="2-4 bullet points supporting a positive view."
        )
        bear_case: list[str] = Field(
            description="2-4 bullet points supporting a negative view."
        )
        catalysts: list[str] = Field(
            description="Upcoming events that could move the stock."
        )
        risks: list[str] = Field(description="Key risks to monitor.")

    llm = get_llm_client()
    structured = llm.with_structured_output(StockAssessment)

    ticker = state["ticker"]
    headlines = _summarize_headlines(state.get("news", []))
    price_line = _summarize_prices(state.get("prices", {}))
    earnings_line = _summarize_earnings(state.get("earnings", {}))
    rag_context = state.get("rag_context", "") or "(no retrieval context available)"
    rag_query = state.get("rag_query", "")

    system_msg = (
        f"You are an equity analyst writing a near-term assessment of {ticker}. "
        "STRICT RULES:\n"
        f"  1. Every bullet MUST reference a specific signal from the INPUT section "
        f"below (a headline, price move, earnings date, or 10-K passage).\n"
        f"  2. NEVER attribute an event to {ticker} if the signal names a different "
        f"company. If a headline is about another company, it is context only — "
        f"never treat it as a {ticker} event.\n"
        "  3. NEVER fabricate numbers, acquisitions, product launches, or quotes. "
        "If a claim is not directly supported by the input signals, do not make it.\n"
        f"  4. If a section (bull / bear / catalysts / risks) has no supporting "
        f"signal, return a single bullet: 'Insufficient data in current signals.'\n"
    )

    prompt = (
        f"=== INPUT SIGNALS FOR {ticker} ===\n\n"
        f"PRICE ACTION: {price_line}\n"
        f"UPCOMING EARNINGS: {earnings_line}\n\n"
        f"{ticker}-SPECIFIC HEADLINES (already filtered to ones that name the company):\n"
        f"{headlines}\n\n"
        f"{ticker} 10-K RETRIEVAL (query: {rag_query!r}):\n{rag_context}\n\n"
        f"=== END INPUT SIGNALS ===\n\n"
        f"Produce a grounded near-term assessment of {ticker}. Each bullet must "
        f"cite one specific signal above. Do not invent new facts; do not confuse "
        f"{ticker} with other companies that may appear in the 10-K context."
    )

    result = structured.invoke(
        [
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt),
        ]
    )

    return {"assessment": result.model_dump()}


# ---------------------------------------------------------------------------
# Graph assembly + entry point
# ---------------------------------------------------------------------------


def get_assessment_graph():
    """Build (or reuse) the compiled assessment LangGraph."""
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is not None:
        return _GRAPH_SINGLETON

    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(AssessmentState)
    builder.add_node("fetch_news", _fetch_news_node)
    builder.add_node("fetch_prices", _fetch_prices_node)
    builder.add_node("fetch_earnings", _fetch_earnings_node)
    builder.add_node("build_rag_query", _build_rag_query_node)
    builder.add_node("rag_context", _rag_context_node)
    builder.add_node("synthesize", _synthesize_node)

    builder.add_edge(START, "fetch_news")
    builder.add_edge(START, "fetch_prices")
    builder.add_edge(START, "fetch_earnings")
    builder.add_edge("fetch_news", "build_rag_query")
    builder.add_edge("fetch_prices", "build_rag_query")
    builder.add_edge("fetch_earnings", "build_rag_query")
    builder.add_edge("build_rag_query", "rag_context")
    builder.add_edge("rag_context", "synthesize")
    builder.add_edge("synthesize", END)

    _GRAPH_SINGLETON = builder.compile()
    return _GRAPH_SINGLETON


async def run_stock_assessment(ticker: str = "AAPL") -> dict[str, Any]:
    """Invoke the assessment graph and return the UI-ready payload."""
    graph = get_assessment_graph()
    state = await graph.ainvoke({"ticker": ticker})
    return {
        "ticker": ticker,
        "rag_query": state.get("rag_query", ""),
        "assessment": state.get("assessment", {}),
    }


# ---------------------------------------------------------------------------
# E2E smoke test — `python -m src.agent.stock_assessment`
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import asyncio
    import json
    import time

    async def smoke() -> None:
        banner = "=" * 72
        print(banner)
        print("  E2E stock_assessment smoke test  |  ticker=AAPL")
        print(banner)
        print()

        graph = get_assessment_graph()
        started = time.perf_counter()

        async for step in graph.astream(
            {"ticker": "AAPL"}, stream_mode="updates"
        ):
            for node_name, update in step.items():
                elapsed = time.perf_counter() - started
                print(f"[{elapsed:6.1f}s] ▶ node: {node_name}")
                for key, value in update.items():
                    preview = json.dumps(value, default=str, indent=2)
                    if len(preview) > 800:
                        preview = preview[:800] + f"\n... [+{len(preview) - 800} chars truncated]"
                    indented = "\n".join("        " + line for line in preview.splitlines())
                    print(f"    └─ {key}:")
                    print(indented)
                print()

        total = time.perf_counter() - started
        print(banner)
        print(f"  smoke test complete in {total:.1f}s")
        print(banner)

    asyncio.run(smoke())
