from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, FastAPI, Request, Response

from config import PORTS, REQUEST_TIMEOUT_SECONDS
from discovery import best_route


class ServiceBase:
    name: str
    port: int
    channel: str
    health_endpoint: str = "/health"

    async def check_health(self) -> bool:
        host = await best_route(self.port)
        if not host:
            return False
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(f"http://{host}:{self.port}{self.health_endpoint}")
            return response.status_code < 500
        except (httpx.HTTPError, OSError, TimeoutError):
            return False

    async def proxy_request(self, path: str, method: str, body: bytes | None = None, headers: dict[str, str] | None = None) -> Response:
        host = await best_route(self.port)
        if not host:
            return Response(
                content=f'{{"detail":"{self.name} is not reachable on port {self.port}"}}',
                media_type="application/json",
                status_code=503,
            )
        url = f"http://{host}:{self.port}/{path.lstrip('/')}"
        forwarded_headers = {key: value for key, value in (headers or {}).items() if key.lower() != "host"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                proxied = await client.request(method, url, content=body, headers=forwarded_headers)
            return Response(content=proxied.content, status_code=proxied.status_code, media_type=proxied.headers.get("content-type"))
        except (httpx.HTTPError, OSError, TimeoutError):
            return Response(
                content=f'{{"detail":"{self.name} proxy request failed"}}',
                media_type="application/json",
                status_code=502,
            )

    def status_payload(self, online: bool) -> dict[str, Any]:
        metadata = PORTS.get(self.port, {})
        return {
            "name": self.name,
            "port": self.port,
            "channel": self.channel,
            "online": online,
            "domain": metadata.get("domain"),
            "owner": metadata.get("owner"),
            "description": metadata.get("description"),
        }

    def register_routes(self, app: FastAPI) -> None:
        router = APIRouter(prefix=f"/api/{self.name.lower().replace(' ', '-')}", tags=[self.name])

        @router.get("/health")
        async def health() -> dict[str, Any]:
            return self.status_payload(await self.check_health())

        @router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy(path: str, request: Request) -> Response:
            return await self.proxy_request(path, request.method, await request.body(), dict(request.headers))

        app.include_router(router)
