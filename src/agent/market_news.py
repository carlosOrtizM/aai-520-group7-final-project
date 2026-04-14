"""Market news provider — Finnhub fetch + LangGraph sentiment/category.

Ported from g(old)/session_init/market_news_provider.py. Original was
class-based with side effects in __init__; here it's a thin async
wrapper that constructs the graph once and reuses it across calls.
"""

from typing import Any, Literal

from src.config import FINNHUB_API_KEY

_GRAPH_SINGLETON = None
_FINNHUB_CLIENT = None


def _get_finnhub_client():
    global _FINNHUB_CLIENT
    if _FINNHUB_CLIENT is not None:
        return _FINNHUB_CLIENT
    import finnhub

    _FINNHUB_CLIENT = finnhub.Client(api_key=FINNHUB_API_KEY)
    return _FINNHUB_CLIENT


def fetch_news(category: Literal["general", "forex", "crypto", "merger"] = "general") -> list[dict]:
    """Fetch raw macro news articles from Finnhub for the given category."""
    client = _get_finnhub_client()
    return client.general_news(category=category) or []


def fetch_company_news(symbol: str, lookback_days: int = 7) -> list[dict]:
    """Fetch ticker-specific news from Finnhub over the last ``lookback_days``.

    Unlike ``fetch_news`` (which hits Finnhub's ``general_news`` endpoint and
    returns macro headlines), this calls ``company_news`` scoped to a single
    symbol. Used by the stock assessment graph so the downstream query builder
    and synthesizer stay anchored on the requested ticker instead of drifting
    onto unrelated names that happen to appear in the macro feed.
    """
    from datetime import datetime, timedelta, timezone

    client = _get_finnhub_client()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=lookback_days)
    return (
        client.company_news(
            symbol,
            _from=start.strftime("%Y-%m-%d"),
            to=now.strftime("%Y-%m-%d"),
        )
        or []
    )


def _build_graph():
    """Build the per-article sentiment/category/summary graph."""
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is not None:
        return _GRAPH_SINGLETON

    from langchain_core.messages import HumanMessage, SystemMessage
    from langgraph.constants import START
    from langgraph.graph import END, StateGraph
    from pydantic import BaseModel, Field
    from typing import TypedDict

    from src.agent.llm_loader import get_llm_client

    llm = get_llm_client()

    class State(TypedDict):
        news_article: str
        sentiment: str
        label: str
        bullets: str

    class NewsSentiment(BaseModel):
        sentiment: Literal["positive", "negative", "neutral"] = Field(
            description="Overall sentiment for the article."
        )

    class NewsCategory(BaseModel):
        label: Literal["inflation", "rates", "fed", "macro", "other"] = Field(
            description="Best matching macro category for the article."
        )

    sentimenter_llm = llm.with_structured_output(NewsSentiment)
    categorizer_llm = llm.with_structured_output(NewsCategory)

    def sentimenter(state: State):
        out = sentimenter_llm.invoke(
            [
                SystemMessage(content="You classify financial news sentiment."),
                HumanMessage(content=f"News article: {state['news_article']}"),
            ]
        )
        return {"sentiment": out.sentiment}

    def categorizer(state: State):
        out = categorizer_llm.invoke(
            [
                SystemMessage(content="You categorize financial news into macro buckets."),
                HumanMessage(content=f"News article: {state['news_article']}"),
            ]
        )
        return {"label": out.label}

    def synthesizer(state: State):
        out = llm.invoke(
            [
                SystemMessage(
                    content="Provide a tight bullet-point summary of the news "
                    "article. Capture the key ideas, no fluff."
                ),
                HumanMessage(content=f"News article: {state['news_article']}"),
            ]
        )
        return {"bullets": out.content}

    builder = StateGraph(State)
    builder.add_node("sentimenter", sentimenter)
    builder.add_node("categorizer", categorizer)
    builder.add_node("synthesizer", synthesizer)
    builder.add_edge(START, "sentimenter")
    builder.add_edge(START, "categorizer")
    builder.add_edge(START, "synthesizer")
    builder.add_edge("sentimenter", END)
    builder.add_edge("categorizer", END)
    builder.add_edge("synthesizer", END)

    _GRAPH_SINGLETON = builder.compile()
    return _GRAPH_SINGLETON


async def summarize_market_news(
    category: Literal["general", "forex", "crypto", "merger"] = "general",
    limit: int = 8,
) -> dict[str, Any]:
    """Fetch news, run them through the graph, and return aggregate stats.

    Args:
        category: Finnhub news category.
        limit: Cap on number of articles to process (LLM cost control).

    Returns:
        Dict with raw articles, per-article analyses, and category counts.
    """
    raw = fetch_news(category)[:limit]
    graph = _build_graph()

    sentiment_by_category = {
        "inflation": [],
        "rates": [],
        "fed": [],
        "macro": [],
        "other": [],
    }
    analyses = []

    for article in raw:
        headline = article.get("headline", "")
        summary = article.get("summary", "")
        prompt_text = f"{headline}: {summary}"
        state = await graph.ainvoke({"news_article": prompt_text})

        analyses.append(
            {
                "headline": headline,
                "url": article.get("url", ""),
                "sentiment": state.get("sentiment"),
                "label": state.get("label"),
                "bullets": state.get("bullets", ""),
            }
        )
        label = state.get("label", "other")
        sentiment_by_category.setdefault(label, []).append(state.get("sentiment"))

    return {
        "category": category,
        "n_articles": len(analyses),
        "analyses": analyses,
        "sentiment_by_category": sentiment_by_category,
    }
