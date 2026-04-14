"""Ollama LLM client loader.

Ported from g(old)/session_init/llm_loader.py. Uses a module-level
singleton so subsequent calls return the same client instance.
"""

from src.config import TEXT_MODEL

_LLM_SINGLETON = None


def get_llm_client():
    """Return a cached ChatOllama client.

    Lazy-imports ``langchain_ollama`` so the agent service starts even
    when the LLM stack is not installed; raises a clear error on first
    use if the dep is missing or Ollama is not reachable.
    """
    global _LLM_SINGLETON
    if _LLM_SINGLETON is not None:
        return _LLM_SINGLETON

    try:
        from langchain_ollama import ChatOllama
    except ImportError as e:
        raise RuntimeError(
            "langchain_ollama is not installed — run `pip install langchain-ollama`"
        ) from e

    _LLM_SINGLETON = ChatOllama(model=TEXT_MODEL, temperature=0.2)
    return _LLM_SINGLETON
