"""ChromaDB persistent vector store.

Ported from g(old)/session_init/chroma_generator.py. Embeddings come
from an Ollama model. The store is persisted under
``persistence/chroma/`` so it survives restarts (no shutil.rmtree on
exit, unlike the original application.py).
"""

import os
import uuid
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


def ingest_documents(documents) -> int:
    """Embed and persist a batch of langchain Documents.

    Args:
        documents: list of lists of langchain Documents (the shape
            returned by pdf_loader.directory_iterator).

    Returns:
        Number of chunks inserted.
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
    ids = [str(uuid.uuid4()) for _ in flat]
    store.add_documents(documents=flat, ids=ids)
    return len(flat)
