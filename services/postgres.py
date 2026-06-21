from __future__ import annotations

from typing import Any

import asyncpg

from config import POSTGRES_TARGETS
from .simple import StaticService


class PostgresService(StaticService):
    def __init__(self, target_key: str) -> None:
        target = POSTGRES_TARGETS[target_key]
        super().__init__(target["name"], target["port"], target_key.upper())
        self.target_key = target_key
        self.role = target["role"]
        self.dsn = target["dsn"]
        self.last_error: str | None = None

    async def check_health(self) -> bool:
        self.last_error = None
        if not self.dsn:
            self.last_error = "DSN not configured"
            return False
        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(self.dsn, timeout=3)
            await conn.execute("SELECT 1")
            return True
        except Exception as exc:
            self.last_error = exc.__class__.__name__
            return False
        finally:
            if conn is not None:
                await conn.close()

    def status_payload(self, online: bool) -> dict[str, Any]:
        payload = super().status_payload(online)
        payload.update(
            {
                "target": self.target_key,
                "role": self.role,
                "configured": bool(self.dsn),
                "detail": "reachable" if online else self.last_error or "not reachable",
            }
        )
        return payload
