from __future__ import annotations

import asyncio
import subprocess
import zlib
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from db import get_clips, save_clip
from .simple import StaticService


class ClipCreate(BaseModel):
    content: str
    chi_score: float | None = None
    vector: Any = None
    tags: list[str] = Field(default_factory=list)


class ClipboardService(StaticService):
    def __init__(self) -> None:
        super().__init__("Clipboard", 28288, "Q")
        self.clients: set[WebSocket] = set()
        self._last_clip: str | None = None

    def classify(self, content: str) -> float:
        return min(1.0, max(0.0, len(content.strip()) / 1000.0))

    def compress(self, content: str) -> str:
        return zlib.compress(content.encode()).hex()

    async def poll_windows_clipboard(self) -> None:
        while True:
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                content = result.stdout.strip()
                if content and content != self._last_clip:
                    self._last_clip = content
                    clip = await save_clip(content, self.classify(content), None, ["clipboard"], self.compress(content))
                    await self.broadcast(clip)
            except (OSError, subprocess.SubprocessError):
                pass
            await asyncio.sleep(2)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        for client in set(self.clients):
            try:
                await client.send_json(payload)
            except RuntimeError:
                self.clients.discard(client)

    def register_routes(self, app: FastAPI) -> None:
        super().register_routes(app)

        @app.get("/api/clips", tags=[self.name])
        async def list_clips(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
            return await get_clips(limit, offset)

        @app.post("/api/clips", tags=[self.name])
        async def create_clip(payload: ClipCreate) -> dict[str, Any]:
            clip = await save_clip(payload.content, payload.chi_score if payload.chi_score is not None else self.classify(payload.content), payload.vector, payload.tags, self.compress(payload.content))
            await self.broadcast(clip)
            return clip

        @app.get("/api/clips/search", tags=[self.name])
        async def search_clips(q: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
            return await get_clips(limit, offset, q)

        @app.websocket("/ws/clips")
        async def clips_ws(websocket: WebSocket) -> None:
            await websocket.accept()
            self.clients.add(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            finally:
                self.clients.discard(websocket)
