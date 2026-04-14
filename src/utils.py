import asyncio
import functools
import glob
import logging
import os
import time
from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class ServiceRequest(BaseModel):
    """Shared request model for inter-service communication.

    Both UI and agent services pack/unpack with this same structure.
    `data` carries the payload (query, ticker, etc.); `params` holds
    metadata (history limits, model overrides, batch flags, ...).
    """

    data: dict = Field(default_factory=dict)
    params: dict = Field(default_factory=dict)


def create_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """Create a per-service logger.

    Console: ERROR only. File: INFO and above, written to
    ``logs/<name>_<date>.txt``. Stale logs (>1 day old) are deleted
    on creation.
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
        _cleanup_old_logs(log_dir)

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if logger.handlers:
            return logger

        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        today = datetime.now().strftime("%Y-%m-%d")
        fh = logging.FileHandler(os.path.join(log_dir, f"{name}_{today}.txt"))
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        return logger

    except Exception as e:
        fallback = logging.getLogger(name)
        fallback.warning(f"Logger setup failed: {e}")
        return fallback


def _cleanup_old_logs(log_dir: str) -> None:
    cutoff = time.time() - timedelta(days=1).total_seconds()
    for path in glob.glob(os.path.join(log_dir, "*.txt")):
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass


def log_call(logger: logging.Logger):
    """Decorator that logs function name, file, and elapsed time at INFO."""

    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info(f"{fn.__name__} | {fn.__code__.co_filename} | {elapsed:.4f}s")
                return result
            except Exception as e:
                logger.error(f"{fn.__name__} | {fn.__code__.co_filename} | {e}")
                raise

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info(f"{fn.__name__} | {fn.__code__.co_filename} | {elapsed:.4f}s")
                return result
            except Exception as e:
                logger.error(f"{fn.__name__} | {fn.__code__.co_filename} | {e}")
                raise

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator
