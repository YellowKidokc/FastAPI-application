from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, FastAPI, Request, Response

from config import REQUEST_TIMEOUT_SECONDS
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
            return Response(content="null", media_type="application/json", status_code=200)
        url = f"http://{host}:{self.port}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                proxied = await client.request(method, url, content=body, headers=headers)
            return Response(content=proxied.content, status_code=proxied.status_code, media_type=proxied.headers.get("content-type"))
        except (httpx.HTTPError, OSError, TimeoutError):
            return Response(content="null", media_type="application/json", status_code=200)

    def status_payload(self, online: bool) -> dict[str, Any]:
        return {"name": self.name, "port": self.port, "channel": self.channel, "online": online}

    def register_routes(self, app: FastAPI) -> None:
        router = APIRouter(prefix=f"/api/{self.name.lower().replace(' ', '-')}", tags=[self.name])

        @router.get("/health")
        async def health() -> dict[str, Any]:
            return self.status_payload(await self.check_health())

        @router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy(path: str, request: Request) -> Response:
            return await self.proxy_request(path, request.method, await request.body(), dict(request.headers))

        app.include_router(router)
