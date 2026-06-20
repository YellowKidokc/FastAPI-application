from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api_assistant import (
    AssistantRequest,
    AssistantResponse,
    classify_action,
    summarize_postgres,
    summarize_statuses,
    summarize_synology,
)
from config import APP_HOST, APP_PORT, PORTS, PORT_RANGES, service_catalog
from db import init_db, sync_loop
from discovery import discover_topology
from security import auth_middleware
from services import SERVICES

startup_topology: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global startup_topology
    await init_db()
    app.state.discovery_task = asyncio.create_task(_warm_topology())
    app.state.sync_task = asyncio.create_task(sync_loop())
    clipboard = next((service for service in SERVICES if service.name == "Clipboard"), None)
    if clipboard is not None:
        app.state.clipboard_task = asyncio.create_task(clipboard.poll_windows_clipboard())
    yield
    for task_name in ("discovery_task", "sync_task", "clipboard_task"):
        task = getattr(app.state, task_name, None)
        if task:
            task.cancel()


app = FastAPI(
    title="POF 2828 Master API",
    description="Master orchestrator for laptop, Synology, Cloudflare, clipboard, NLP, and preference services",
    version="0.2.0",
    lifespan=lifespan,
)
app.middleware("http")(auth_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for service in SERVICES:
    service.register_routes(app)


async def _warm_topology() -> None:
    global startup_topology
    startup_topology = await discover_topology()


@app.get("/health")
async def health() -> dict[str, Any]:
    service_status = await _service_statuses()
    return {
        "status": "ok",
        "master": {"host": APP_HOST, "port": APP_PORT},
        "ports": {str(port): _port_status(port, service_status) for port in PORTS},
    }


@app.get("/services")
async def services() -> list[dict[str, Any]]:
    return await _service_statuses()


@app.get("/ports")
async def ports() -> dict[str, Any]:
    return {
        "ranges": [port_range.__dict__ for port_range in PORT_RANGES],
        "services": service_catalog(),
    }


@app.get("/topology")
async def topology() -> dict[str, Any]:
    return await discover_topology()


@app.post("/api/assistant")
async def api_assistant(payload: AssistantRequest) -> AssistantResponse:
    action = classify_action(payload.message)

    if action == "postgres_status":
        statuses = await _service_statuses(("PostgreSQL Main", "PostgreSQL Memory", "PostgreSQL Analytics"))
        return AssistantResponse(answer=summarize_postgres(statuses), action=action, data=statuses)
    if action == "synology_status":
        statuses = await _service_statuses(("Synology API",))
        return AssistantResponse(answer=summarize_synology(statuses), action=action, data=statuses)
    if action == "topology":
        topology_payload = await discover_topology()
        return AssistantResponse(answer="Here is the current machine and route topology.", action=action, data=topology_payload)
    if action == "ports":
        return AssistantResponse(answer="Here is the current port and API plan.", action=action, data=service_catalog())
    if action == "clipboard":
        return AssistantResponse(answer="Clipboard APIs are available at /api/clips and /ws/clips.", action=action, data=None)

    statuses = await _service_statuses()
    return AssistantResponse(answer=summarize_statuses(statuses), action=action, data=statuses)


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    statuses = await _service_statuses()
    catalog = service_catalog()
    cards = "".join(
        f"<article class='card {'up' if item['online'] else 'down'}'><h2>{item['name']}</h2>"
        f"<p>Port {item['port']} | Channel {item['channel']}</p>"
        f"<strong>{'ONLINE' if item['online'] else 'OFFLINE'}</strong></article>"
        for item in statuses
    )
    port_rows = "".join(
        f"<tr><td>{item['port']}</td><td>{item['name']}</td><td>{item['domain']}</td>"
        f"<td>{item['owner']}</td><td>{item['description']}</td></tr>"
        for item in catalog
    )
    return f"""
    <!doctype html><html><head><title>POF 2828 Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #101820; color: #f7f9fb; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
      .card {{ border-radius: 8px; padding: 1rem; border: 1px solid #34404d; }}
      .up {{ background: #12543f; }} .down {{ background: #6f2430; }}
      .cockpit {{ display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 1rem; align-items: start; }}
      .panel {{ border: 1px solid #34404d; border-radius: 8px; padding: 1rem; background: #18232e; }}
      textarea {{ width: 100%; min-height: 110px; resize: vertical; box-sizing: border-box; background: #0d141c; color: #f7f9fb; border: 1px solid #34404d; border-radius: 8px; padding: .75rem; font: inherit; }}
      button {{ margin-top: .75rem; border: 0; border-radius: 8px; background: #2e7db5; color: white; padding: .65rem .9rem; font-weight: 700; cursor: pointer; }}
      pre {{ white-space: pre-wrap; background: #0d141c; border: 1px solid #34404d; border-radius: 8px; padding: .75rem; min-height: 80px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 1.25rem; }}
      th, td {{ border-bottom: 1px solid #34404d; padding: .55rem; text-align: left; vertical-align: top; }}
      h1, h2 {{ margin-top: 0; }} a {{ color: #8dc6ff; }}
      @media (max-width: 900px) {{ body {{ margin: 1rem; }} .cockpit {{ grid-template-columns: 1fr; }} table {{ font-size: .9rem; }} }}
    </style></head><body><h1>POF 2828 API Cockpit</h1><p><a href='/services'>JSON services</a> | <a href='/health'>Health</a> | <a href='/ports'>Port plan</a></p><main class='cockpit'><section><section class='grid'>{cards}</section><h2>Port Plan</h2><table><thead><tr><th>Port</th><th>Service</th><th>Domain</th><th>Owner</th><th>Description</th></tr></thead><tbody>{port_rows}</tbody></table></section><aside class='panel'><h2>Assistant</h2><textarea id='prompt' placeholder='Ask about Postgres, Synology, ports, topology, clipboard, or status'></textarea><button id='ask'>Ask API</button><pre id='answer'>Ready.</pre></aside></main><script>
      const promptEl = document.getElementById('prompt');
      const answerEl = document.getElementById('answer');
      document.getElementById('ask').addEventListener('click', async () => {{
        const message = promptEl.value.trim();
        if (!message) return;
        answerEl.textContent = 'Working...';
        try {{
          const response = await fetch('/api/assistant', {{
            method: 'POST',
            headers: {{ 'content-type': 'application/json' }},
            body: JSON.stringify({{ message }})
          }});
          const payload = await response.json();
          answerEl.textContent = payload.answer + "\\n\\nAction: " + payload.action;
        }} catch (error) {{
          answerEl.textContent = 'Assistant request failed: ' + error;
        }}
      }});
    </script></body></html>
    """


async def _service_statuses(names: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    services = [service for service in SERVICES if names is None or service.name in names]
    statuses = await asyncio.gather(*(service.check_health() for service in services), return_exceptions=True)
    return [
        service.status_payload(bool(status) if not isinstance(status, Exception) else False)
        for service, status in zip(services, statuses)
    ]


def _port_status(port: int, statuses: list[dict[str, Any]]) -> dict[str, Any]:
    registered = next((status for status in statuses if status["port"] == port), None)
    return {**PORTS[port], "online": True if port == APP_PORT else bool(registered and registered["online"])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=False)
