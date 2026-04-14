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
_CLASSIFIER_LLM = None

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
    """Pull ticker-specific headlines from Finnhub and filter for relevance.

    Two-stage filter. First, a cheap substring check against ``_TICKER_ALIASES``
    drops the bulk of the Finnhub feed that doesn't mention the ticker
    anywhere (248 → ~30 articles for AAPL on a typical day). Second, a per
    article LLM classifier drops stories that name the ticker only in
    passing — an Amazon/Globalstar deal whose summary says "with Apple",
    or a ByBit crypto article listing Apple as a tradeable stock. Both
    patterns bypassed the pure-substring filter and were hijacking
    downstream synthesis.

    Finnhub's ``related`` field is not usable for filtering: ``company_news``
    echoes the requested symbol back on every article it returns,
    including obvious drift stories, so there's nothing authoritative
    to key off of except the text itself.
    """
    try:
        from src.agent.market_news import fetch_company_news

        ticker = state["ticker"]
        raw = fetch_company_news(ticker, lookback_days=7)
        candidates = [a for a in raw if _headline_mentions_ticker(a, ticker)][:12]
        relevant = _llm_filter_relevant_news(candidates, ticker)[:6]
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


def _get_classifier_llm():
    """Dedicated deterministic LLM client for the relevance filter.

    Separate from ``get_llm_client`` because that singleton is cached at
    ``temperature=0.2`` for generative work (query builder + synthesizer),
    and a non-zero temperature was causing the classifier to flip its
    verdict on the same article across runs. A fresh ``ChatOllama`` at
    ``temperature=0`` is deterministic and cheap to keep around.
    """
    global _CLASSIFIER_LLM
    if _CLASSIFIER_LLM is not None:
        return _CLASSIFIER_LLM

    from langchain_ollama import ChatOllama

    from src.config import TEXT_MODEL

    _CLASSIFIER_LLM = ChatOllama(model=TEXT_MODEL, temperature=0)
    return _CLASSIFIER_LLM


def _llm_filter_relevant_news(articles: list[dict], ticker: str) -> list[dict]:
    """Per-article LLM relevance classifier.

    Uses a plain YES/NO prompt instead of ``with_structured_output``
    because llama3.2 is weak at function-calling / JSON-schema output
    and was flipping verdicts on borderline cases. String parsing on a
    one-word answer is both more reliable and faster on this model.
    Fails open so an Ollama hiccup can't silently delete all news.
    """
    if not articles:
        return articles

    from langchain_core.messages import HumanMessage, SystemMessage

    llm = _get_classifier_llm()
    system_msg = (
        f"You filter financial news for {ticker}. Answer with exactly one "
        f"word: YES or NO. YES only when the article is substantively about "
        f"{ticker} — its products, earnings, guidance, management, stock "
        f"action, legal or regulatory events. NO when {ticker} is named "
        f"only in passing: a partner in someone else's deal, an example of "
        f"a tradeable stock, a comparison, or context for a different "
        f"company's story. When in doubt, answer NO.\n\n"
        f"EXAMPLES:\n"
        f"- 'Apple's Fiscal Q2 Earnings Could Beat Street Consensus' -> YES\n"
        f"- 'Amazon acquiring Globalstar' (summary mentions 'agreement with "
        f"Apple') -> NO (story is about Amazon; Apple is a partner)\n"
        f"- 'ByBit Lets Traders Trade Stocks Like Apple and IBIT' -> NO "
        f"(story is about ByBit; Apple is an example)"
    )

    kept = []
    for article in articles:
        prompt = (
            f"HEADLINE: {article.get('headline', '')}\n"
            f"SUMMARY: {(article.get('summary') or '')[:300]}\n\n"
            f"Is this article substantively about {ticker}? Answer YES or NO."
        )
        try:
            result = llm.invoke(
                [
                    SystemMessage(content=system_msg),
                    HumanMessage(content=prompt),
                ]
            )
            answer = (result.content or "").strip().upper()
            if answer.startswith("YES"):
                kept.append(article)
        except Exception:
            kept.append(article)
    return kept


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
    """Compact one-line price summary with latest TA indicator values.

    ``price_history._try_attach_indicators`` bolts MA/EMA/RSI/ADX/ATR/OBV
    onto every row when TA-Lib is available, but those columns were
    getting dropped on the way into the synthesizer — only the close
    prices were surviving into the prompt. That left the model with
    nothing technical to reason about (no trend strength, no momentum,
    no volatility regime). This summary now appends the most recent
    non-NaN value of each indicator, with a quick above/below flag
    versus the 10-day moving averages so llama3.2 doesn't have to do
    the comparison itself.
    """
    data = prices.get("data", [])
    if not data:
        return "(no price data)"
    closes = [r.get("Close") for r in data if r.get("Close") is not None]
    if not closes:
        return "(no close prices)"
    last = closes[-1]
    first = closes[0]
    pct = ((last - first) / first * 100) if first else 0.0
    base = f"{len(closes)} sessions: ${first:,.2f} → ${last:,.2f} ({pct:+.1f}%)"

    latest_row = data[-1]

    def _num(val):
        """Return ``val`` as a float or ``None`` for missing/NaN values."""
        if val is None:
            return None
        try:
            f = float(val)
        except (TypeError, ValueError):
            return None
        # NaN is the only float that is not equal to itself.
        return f if f == f else None

    ma = _num(latest_row.get("MA"))
    ema = _num(latest_row.get("EMA"))
    rsi = _num(latest_row.get("RSI"))
    adx = _num(latest_row.get("ADX"))
    atr = _num(latest_row.get("ATR"))
    obv = _num(latest_row.get("OBV"))

    ta_parts: list[str] = []
    if ma is not None:
        side = "above" if last >= ma else "below"
        ta_parts.append(f"MA10=${ma:,.2f} (price {side})")
    if ema is not None:
        side = "above" if last >= ema else "below"
        ta_parts.append(f"EMA10=${ema:,.2f} (price {side})")
    if rsi is not None:
        ta_parts.append(f"RSI14={rsi:.1f}")
    if adx is not None:
        ta_parts.append(f"ADX10={adx:.1f}")
    if atr is not None:
        ta_parts.append(f"ATR14=${atr:,.2f}")
    if obv is not None:
        ta_parts.append(f"OBV={obv:,.0f}")

    if ta_parts:
        return f"{base} | " + ", ".join(ta_parts)
    return base


_HOUR_LABELS = {
    "amc": "after market close",
    "bmo": "before market open",
    "dmh": "during market hours",
}


def _fmt_revenue(val) -> str:
    """Render a Finnhub revenue estimate as a compact dollar string."""
    try:
        n = float(val)
    except (TypeError, ValueError):
        return "N/A"
    if n != n:  # NaN
        return "N/A"
    if abs(n) >= 1e9:
        return f"${n / 1e9:.1f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.1f}M"
    return f"${n:,.0f}"


def _fmt_eps(val) -> str:
    try:
        n = float(val)
    except (TypeError, ValueError):
        return "N/A"
    if n != n:
        return "N/A"
    return f"${n:,.2f}"


def _format_earnings_event(event: dict) -> str:
    """One-line render of a single Finnhub earnings calendar entry."""
    date = event.get("date", "?")
    quarter = event.get("quarter")
    year = event.get("year")
    hour = event.get("hour", "")
    hour_label = _HOUR_LABELS.get(hour, hour or "time TBD")
    eps = _fmt_eps(event.get("epsEstimate"))
    rev = _fmt_revenue(event.get("revenueEstimate"))

    period = (
        f"fiscal Q{quarter} {year}"
        if quarter and year
        else "upcoming quarter"
    )
    return (
        f"{period} on {date} ({hour_label}) — "
        f"EPS est {eps}, revenue est {rev}"
    )


def _summarize_earnings(earnings: dict) -> str:
    """Chronologically-sorted earnings summary with EPS + revenue estimates.

    Finnhub returns the ``earningsCalendar`` list in an order we can't
    rely on — a 120-day lookahead for AAPL has come back with the
    further-out event first, so taking ``events[0]`` was mislabeling
    the later quarter as "next". Sort ascending by date so the first
    entry is actually the nearest future event. Render up to two
    events so the synthesizer sees both the immediate catalyst and
    the follow-up one if it exists inside the window.
    """
    events = (earnings.get("calendar") or {}).get("earningsCalendar") or []
    if not events:
        return "(no upcoming earnings in window)"

    sorted_events = sorted(events, key=lambda e: e.get("date") or "")
    nxt = _format_earnings_event(sorted_events[0])
    if len(sorted_events) == 1:
        return f"Next: {nxt}"
    then = _format_earnings_event(sorted_events[1])
    return f"Next: {nxt}\nThen: {then}"


def _summarize_headlines(news: list[dict]) -> str:
    """Render headlines plus trimmed summaries for the downstream prompts.

    Headlines alone were giving the synthesizer too little to cite back
    — llama3.2 was leaning on the headline text as the entire claim.
    Including the Finnhub summary (trimmed to keep the prompt bounded)
    gives the model real context to ground its bullets in.
    """
    if not news:
        return "(no headlines)"

    lines: list[str] = []
    for n in news:
        headline = (n.get("headline") or "").strip()
        if not headline:
            continue
        summary = " ".join((n.get("summary") or "").split())
        if len(summary) > 600:
            summary = summary[:600].rstrip() + "…"
        lines.append(f"- {headline}")
        if summary:
            lines.append(f"  {summary}")
    return "\n".join(lines) if lines else "(no headlines)"


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
    if not query:
        # Nothing came back — substitute a generic ticker-anchored query
        # so rag_context always has something to retrieve against.
        query = (
            f"What does {ticker}'s 10-K identify as its primary near-term "
            f"risks and growth drivers?"
        )
    elif ticker.upper() not in query.upper():
        # llama3.2 frequently writes a signal-specific question (e.g.
        # "How is iPhone demand expected to affect services revenue?")
        # without naming the ticker. The previous behavior discarded
        # those outright and fell back to the generic question, which
        # also threw away all the signal-specific targeting. Prepending
        # the ticker preserves the LLM's intent while still guaranteeing
        # the ticker appears in the query text.
        query = f"Regarding {ticker}: {query}"
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
