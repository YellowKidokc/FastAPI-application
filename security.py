from __future__ import annotations

import hmac
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from config import AUTH_ENABLED, CODEX_TOKEN, MASTER_TOKEN

PUBLIC_PATH_PREFIXES = (
    "/",
    "/health",
    "/services",
    "/ports",
    "/topology",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def token_role(token: str | None) -> str | None:
    if not token:
        return None
    if MASTER_TOKEN and hmac.compare_digest(token, MASTER_TOKEN):
        return "master"
    if CODEX_TOKEN and hmac.compare_digest(token, CODEX_TOKEN):
        return "codex"
    return None


def token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return request.headers.get("x-pof-token")


def is_public_path(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in PUBLIC_PATH_PREFIXES if prefix != "/") or path == "/"


async def auth_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    if not AUTH_ENABLED or is_public_path(request.url.path):
        return await call_next(request)

    role = token_role(token_from_request(request))
    if role is None:
        return JSONResponse({"detail": "Missing or invalid POF service token"}, status_code=401)

    request.state.token_role = role
    return await call_next(request)
