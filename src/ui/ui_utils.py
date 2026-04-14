"""Serialization helpers for the UI -> agent bridge."""

from src.utils import ServiceRequest

AGENT_BASE_URL = "http://localhost:8011"


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
        return {"error": str(e)}
