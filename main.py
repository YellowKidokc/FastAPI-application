from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from config import PORTS
from db import init_db, sync_loop
from discovery import discover_topology
from services import SERVICES

startup_topology: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global startup_topology
    await init_db()
    startup_topology = await discover_topology()
    app.state.sync_task = asyncio.create_task(sync_loop())
    clipboard = next((service for service in SERVICES if service.name == "Clipboard"), None)
    if clipboard is not None:
        app.state.clipboard_task = asyncio.create_task(clipboard.poll_windows_clipboard())
    yield
    for task_name in ("sync_task", "clipboard_task"):
        task = getattr(app.state, task_name, None)
        if task:
            task.cancel()


app = FastAPI(title="POF 2828 Master API", description="Master orchestrator for POF 2828 services", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for service in SERVICES:
    service.register_routes(app)


@app.get("/health")
async def health() -> dict[str, Any]:
    service_status = await _service_statuses()
    return {"status": "ok", "ports": {str(port): _port_status(port, service_status) for port in PORTS}}


@app.get("/services")
async def services() -> list[dict[str, Any]]:
    return await _service_statuses()


@app.get("/topology")
async def topology() -> dict[str, Any]:
    return await discover_topology()


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    statuses = await _service_statuses()
    cards = "".join(
        f"<article class='card {'up' if item['online'] else 'down'}'><h2>{item['name']}</h2>"
        f"<p>Port {item['port']} · Channel {item['channel']}</p>"
        f"<strong>{'ONLINE' if item['online'] else 'OFFLINE'}</strong></article>"
        for item in statuses
    )
    return f"""
    <!doctype html><html><head><title>POF 2828 Dashboard</title>
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #111827; color: #f9fafb; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
      .card {{ border-radius: 1rem; padding: 1rem; border: 1px solid #374151; }}
      .up {{ background: #064e3b; }} .down {{ background: #7f1d1d; }}
      h1, h2 {{ margin-top: 0; }} a {{ color: #93c5fd; }}
    </style></head><body><h1>POF 2828 Master API</h1><p><a href='/services'>JSON services</a> · <a href='/health'>Health</a></p><section class='grid'>{cards}</section></body></html>
    """


async def _service_statuses() -> list[dict[str, Any]]:
    statuses = await asyncio.gather(*(service.check_health() for service in SERVICES), return_exceptions=True)
    return [
        service.status_payload(bool(status) if not isinstance(status, Exception) else False)
        for service, status in zip(SERVICES, statuses)
    ]


def _port_status(port: int, statuses: list[dict[str, Any]]) -> dict[str, Any]:
    registered = next((status for status in statuses if status["port"] == port), None)
    return {**PORTS[port], "online": True if port == 28280 else bool(registered and registered["online"])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=28280, reload=False)
