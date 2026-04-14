"""Validation + request-unpacking helpers for the agent service."""

from datetime import datetime

from src.utils import ServiceRequest


def unpack_request(req: ServiceRequest) -> ServiceRequest:
    """Pass-through unpacker — extension point for validation/feature work."""
    return req


def validate_ticker(ticker: str) -> bool:
    return bool(ticker) and ticker.replace(".", "").replace("-", "").isalnum()


def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False
