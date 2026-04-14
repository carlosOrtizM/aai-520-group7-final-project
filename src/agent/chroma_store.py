"""ChromaDB persistent vector store.

Ported from g(old)/session_init/chroma_generator.py. Embeddings come
from an Ollama model. The store is persisted under
``persistence/chroma/`` so it survives restarts (no shutil.rmtree on
exit, unlike the original application.py).
"""

import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PERSISTENCE_PATH = os.getenv("PERSISTENCE_PATH", "persistence")
_VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "chroma")
_COLLECTION = os.getenv("CHROMA_COLLECTION", "financial-collection")
_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embeddinggemma:latest")

CHROMA_DIRECTORY = str(_PROJECT_ROOT / _PERSISTENCE_PATH / _VECTOR_DB_PATH)

_VECTOR_STORE = None


def _embedder():
    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=_EMBEDDING_MODEL)


def get_vector_store():
    """Return a cached Chroma vector store, opening or creating it on disk."""
    global _VECTOR_STORE
    if _VECTOR_STORE is not None:
        return _VECTOR_STORE

    try:
        from chromadb.config import Settings
        from langchain_chroma import Chroma
    except ImportError as e:
        raise RuntimeError(
            "langchain_chroma / chromadb are not installed"
        ) from e

    os.makedirs(CHROMA_DIRECTORY, exist_ok=True)
    _VECTOR_STORE = Chroma(
        collection_name=_COLLECTION,
        embedding_function=_embedder(),
        persist_directory=CHROMA_DIRECTORY,
        client_settings=Settings(anonymized_telemetry=False),
    )
    return _VECTOR_STORE


def _chunk_id(chunk) -> str:
    """Stable ID for a chunk — sha256 of (source || content).

    Deterministic IDs make re-ingestion idempotent: the same PDF
    chunked the same way produces the same IDs, so the existence
    check in ``ingest_documents`` can skip them instead of writing
    duplicate embeddings under fresh UUIDs.
    """
    src = chunk.metadata.get("source") or chunk.metadata.get("filename") or ""
    h = hashlib.sha256()
    h.update(str(src).encode("utf-8"))
    h.update(b"\x00")
    h.update(chunk.page_content.encode("utf-8"))
    return h.hexdigest()


def ingest_documents(documents) -> dict:
    """Embed and persist chunks, skipping any already present in the store.

    Args:
        documents: list of lists of langchain Documents (the shape
            returned by pdf_loader.directory_iterator).

    Returns:
        Dict with ``new`` (chunks actually embedded), ``skipped``
        (chunks already indexed), and ``total`` (chunks seen).
    """
    from langchain_core.documents import Document

    store = get_vector_store()
    flat = [
        Document(
            page_content=chunk.page_content,
            metadata=chunk.metadata,
        )
        for doc in documents
        for chunk in doc
    ]
    if not flat:
        return {"new": 0, "skipped": 0, "total": 0}

    ids = [_chunk_id(d) for d in flat]
    existing = store.get(ids=ids)
    existing_ids = set(existing.get("ids") or [])

    new_docs, new_ids = [], []
    for idx, doc in zip(ids, flat):
        if idx in existing_ids:
            continue
        new_ids.append(idx)
        new_docs.append(doc)

    if new_docs:
        store.add_documents(documents=new_docs, ids=new_ids)

    return {
        "new": len(new_docs),
        "skipped": len(flat) - len(new_docs),
        "total": len(flat),
    }
