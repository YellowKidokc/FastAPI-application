from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class AssistantResponse(BaseModel):
    answer: str
    action: str
    data: Any = None


def classify_action(message: str) -> str:
    normalized = message.lower()
    if any(word in normalized for word in ("postgres", "postgress", "pg", "database", "db")):
        return "postgres_status"
    if any(word in normalized for word in ("synology", "nas", "dsm", "file station", "filestation")):
        return "synology_status"
    if any(word in normalized for word in ("topology", "route", "machine", "laptop", "desktop")):
        return "topology"
    if any(word in normalized for word in ("port", "range", "five number", "number")):
        return "ports"
    if any(word in normalized for word in ("clip", "clipboard")):
        return "clipboard"
    return "status"


def summarize_statuses(statuses: list[dict[str, Any]]) -> str:
    up = [item["name"] for item in statuses if item.get("online")]
    down = [item["name"] for item in statuses if not item.get("online")]
    return f"{len(up)} up, {len(down)} down. Up: {', '.join(up) or 'none'}. Down: {', '.join(down) or 'none'}."


def summarize_postgres(statuses: list[dict[str, Any]]) -> str:
    postgres = [item for item in statuses if str(item.get("name", "")).startswith("PostgreSQL")]
    if not postgres:
        return "No PostgreSQL services are registered yet."
    parts = [
        f"{item['name']} is {'up' if item.get('online') else 'down'} ({item.get('detail', 'no detail')})"
        for item in postgres
    ]
    return "; ".join(parts) + "."


def summarize_synology(statuses: list[dict[str, Any]]) -> str:
    synology = next((item for item in statuses if item.get("name") == "Synology API"), None)
    if not synology:
        return "Synology API is not registered yet."
    return f"Synology API is {'up' if synology.get('online') else 'down'} ({synology.get('detail', 'no detail')})."
