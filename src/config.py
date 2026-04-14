"""Centralized configuration & environment loading.

Single source of truth for every ``.env`` knob the two services
care about. Importing from here (instead of calling ``os.getenv``
inline in five modules) keeps defaults and names in one place, and
lets ``grep src.config`` answer "what is configurable?" in one shot.

``load_dotenv`` runs once at module import time — any subsequent
``from src.config import X`` just reads the already-cached constant.
Adding a new knob is a one-line addition here plus a matching line
in ``.env.example``.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths (resolved relative to the project root so the services work no matter
# what the current working directory is when main.py spawns them)
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

PERSISTENCE_PATH: str = os.getenv("PERSISTENCE_PATH", "persistence")
VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "chroma")
KB_PATH: str = os.getenv("KB_PATH", "reference_files")

CHROMA_DIRECTORY: Path = PROJECT_ROOT / PERSISTENCE_PATH / VECTOR_DB_PATH
KB_DIRECTORY: Path = PROJECT_ROOT / PERSISTENCE_PATH / KB_PATH

# ---------------------------------------------------------------------------
# Chroma
# ---------------------------------------------------------------------------
CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "financial-collection")

# ---------------------------------------------------------------------------
# Ollama models (must already be pulled locally: `ollama pull ...`)
# ---------------------------------------------------------------------------
TEXT_MODEL: str = os.getenv("TEXT_MODEL", "llama3.2:latest")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "embeddinggemma:latest")

# ---------------------------------------------------------------------------
# Upstream APIs
# ---------------------------------------------------------------------------
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

# ---------------------------------------------------------------------------
# Inter-service
# ---------------------------------------------------------------------------
AGENT_BASE_URL: str = os.getenv("AGENT_BASE_URL", "http://localhost:8011")


def missing_required() -> list[str]:
    """Return the names of empty-but-required config values.

    Called at agent service boot so missing keys surface as one clear
    log warning instead of as mysteriously empty Finnhub responses
    three minutes into an assessment run.
    """
    missing: list[str] = []
    if not FINNHUB_API_KEY:
        missing.append("FINNHUB_API_KEY")
    return missing
