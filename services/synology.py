from __future__ import annotations

import asyncio
from typing import Any

from config import (
    SYNOLOGY_CERT_VERIFY,
    SYNOLOGY_DSM_VERSION,
    SYNOLOGY_HOST,
    SYNOLOGY_PASSWORD,
    SYNOLOGY_PORT,
    SYNOLOGY_QUICKCONNECT_ID,
    SYNOLOGY_SECURE,
    SYNOLOGY_USERNAME,
)
from .simple import StaticService


class SynologyService(StaticService):
    def __init__(self) -> None:
        super().__init__("Synology API", 28300, "NAS")
        self.last_error: str | None = None

    async def check_health(self) -> bool:
        self.last_error = None
        if not SYNOLOGY_USERNAME or not SYNOLOGY_PASSWORD:
            self.last_error = "credentials not configured"
            return False
        try:
            await asyncio.to_thread(self._get_info)
            return True
        except ModuleNotFoundError:
            self.last_error = "synology-api package not installed"
            return False
        except Exception as exc:
            self.last_error = exc.__class__.__name__
            return False

    def _get_info(self) -> Any:
        from synology_api.filestation import FileStation

        if SYNOLOGY_QUICKCONNECT_ID:
            fs = FileStation(
                quickconnect_id=SYNOLOGY_QUICKCONNECT_ID,
                username=SYNOLOGY_USERNAME,
                password=SYNOLOGY_PASSWORD,
                cert_verify=SYNOLOGY_CERT_VERIFY,
                dsm_version=SYNOLOGY_DSM_VERSION,
                debug=False,
            )
        else:
            fs = FileStation(
                SYNOLOGY_HOST,
                SYNOLOGY_PORT,
                SYNOLOGY_USERNAME,
                SYNOLOGY_PASSWORD,
                secure=SYNOLOGY_SECURE,
                cert_verify=SYNOLOGY_CERT_VERIFY,
                dsm_version=SYNOLOGY_DSM_VERSION,
                debug=False,
            )
        return fs.get_info()

    def status_payload(self, online: bool) -> dict[str, Any]:
        payload = super().status_payload(online)
        payload.update(
            {
                "configured": bool(SYNOLOGY_USERNAME and SYNOLOGY_PASSWORD),
                "host": SYNOLOGY_QUICKCONNECT_ID or SYNOLOGY_HOST,
                "detail": "reachable" if online else self.last_error or "not reachable",
            }
        )
        return payload
