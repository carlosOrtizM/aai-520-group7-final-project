"""Serialization helpers for the UI -> agent bridge."""

from src.config import AGENT_BASE_URL
from src.utils import ServiceRequest

__all__ = ["AGENT_BASE_URL", "pack_request", "pack_request_with_params", "send_to_agent"]


def pack_request(**data) -> ServiceRequest:
    """Wrap ``data`` kwargs in a ServiceRequest with no extra params."""
    return ServiceRequest(data=data, params={})


def pack_request_with_params(data: dict, params: dict) -> ServiceRequest:
    return ServiceRequest(data=data, params=params)


async def send_to_agent(session, payload: ServiceRequest, endpoint: str) -> dict:
    """POST ``payload`` to ``endpoint`` on the agent service."""
    url = f"{AGENT_BASE_URL}{endpoint}"
    try:
        async with session.post(url, json=payload.model_dump()) as resp:
            return await resp.json()
    except Exception as e:
        # asyncio.TimeoutError stringifies to "" — fall back to the class
        # name so the UI error card shows something meaningful instead of
        # rendering "Assessment: " with no message.
        msg = str(e) or type(e).__name__
        return {"error": msg}
