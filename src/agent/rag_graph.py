"""10-K retrieval helper.

Pure retrieval over the persistent Chroma store — no LLM synthesis.
Callers (today: the ``rag_context`` node in ``stock_assessment.py``)
feed the returned chunks into their own prompt alongside other
signals. The previous LangGraph RAG pipeline (``get_rag_graph`` /
``run_rag_query``) was removed when the chat box moved from free-form
Q&A to the deterministic assessment flow.
"""


def retrieve_10k_context(query: str, k: int = 5) -> str:
    """Return the top-``k`` 10-K chunks for ``query`` as one annotated string."""
    if not query:
        return ""

    from src.agent.chroma_store import get_vector_store

    store = get_vector_store()
    docs = store.similarity_search(query, k=k)
    return "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}" for doc in docs
    )
