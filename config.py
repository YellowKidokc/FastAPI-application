from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent


def _load_local_env() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = _env(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class PortRange:
    name: str
    start: int
    end: int
    purpose: str

    def contains(self, port: int) -> bool:
        return self.start <= port <= self.end


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    port: int
    channel: str
    domain: str
    owner: str
    description: str
    public_path: str | None = None

    def payload(self) -> dict[str, Any]:
        return asdict(self)


PORT_RANGES: tuple[PortRange, ...] = (
    PortRange("core", 28280, 28289, "Master API, service bridge, and local-first control plane"),
    PortRange("dashboards", 28290, 28299, "Human-facing HTML dashboards and status pages"),
    PortRange("storage", 28300, 28319, "SQLite, PostgreSQL, Synology, backups, and file indexing"),
    PortRange("intelligence", 28320, 28349, "NLP, preference engine, embeddings, ranking, and memory"),
    PortRange("media", 28350, 28369, "TTS, STT, image, video, and lossless compression workers"),
    PortRange("automation", 28370, 28389, "Clipboard, launchers, schedulers, and background daemons"),
    PortRange("network", 28390, 28409, "Cloudflare, tunnels, DNS, webhooks, and external bridges"),
    PortRange("agents", 28410, 28449, "Codex/AI agent workers and experimental services"),
)

SERVICE_SPECS: tuple[ServiceSpec, ...] = (
    ServiceSpec("Master API", 28280, "chi", "core", "laptop-primary", "FastAPI orchestrator and dashboard", "/"),
    ServiceSpec("PostgreSQL proxy", 28281, "G", "storage", "nas-preferred", "Legacy PostgreSQL bridge health checks"),
    ServiceSpec("FIS", 28282, "M", "core", "laptop-primary", "Planned field intelligence service endpoint"),
    ServiceSpec("NLP Pipeline", 28283, "E", "intelligence", "laptop-primary", "Natural-language processing pipeline"),
    ServiceSpec("Dedup daemon", 28284, "S", "automation", "any", "Content de-duplication and normalization daemon"),
    ServiceSpec("TTS", 28285, "T", "media", "laptop-primary", "Text-to-speech worker"),
    ServiceSpec("Lossless Compression", 28286, "K", "media", "any", "Lossless compression utility"),
    ServiceSpec("Comms Hub", 28287, "R", "network", "any", "Cross-device communication hub"),
    ServiceSpec("Clipboard", 28288, "Q", "automation", "laptop-primary", "Clipboard capture, sync, and WebSocket stream"),
    ServiceSpec("Cross-service bridge", 28289, "F", "core", "any", "Internal service-to-service bridge"),
    ServiceSpec("Health dashboard", 28290, "C", "dashboards", "any", "Human-readable status dashboard", "/"),
    ServiceSpec("Synology API", 28300, "NAS", "storage", "nas-primary", "Synology DSM/File Station integration"),
    ServiceSpec("PostgreSQL Main", 28301, "PG1", "storage", "nas-preferred", "Primary relational database"),
    ServiceSpec("PostgreSQL Memory", 28302, "PG2", "storage", "laptop-primary", "Memory, embeddings, and assistant working data"),
    ServiceSpec("PostgreSQL Analytics", 28303, "PG3", "storage", "nas-preferred", "Reporting, event history, and metrics database"),
    ServiceSpec("Preference Engine", 28320, "PREF", "intelligence", "laptop-primary", "Preference scoring, ranking, and personalization"),
    ServiceSpec("Cloudflare Bridge", 28390, "CF", "network", "edge", "Cloudflare tunnel, DNS, and webhook integration"),
    ServiceSpec("Codex Worker", 28410, "AI", "agents", "laptop-primary", "Agent-side automation with constrained service token"),
)

PORTS: dict[int, dict[str, Any]] = {spec.port: spec.payload() for spec in SERVICE_SPECS}
SERVICE_PORTS = tuple(sorted(PORTS))

HOSTS = {
    "desktop": {"lan": _env("POF_DESKTOP_LAN", "192.168.1.76"), "direct": _env("POF_DESKTOP_DIRECT", "192.168.2.51")},
    "nas": {"lan": _env("POF_NAS_LAN", "192.168.1.177"), "direct": _env("POF_NAS_DIRECT", "192.168.2.50")},
    "laptop": {"lan": _env("POF_LAPTOP_LAN"), "direct": _env("POF_LAPTOP_DIRECT")},
}

APP_HOST = _env("POF_APP_HOST", "0.0.0.0") or "0.0.0.0"
APP_PORT = int(_env("POF_APP_PORT", "28280") or "28280")
DASHBOARD_HOST = _env("POF_DASHBOARD_HOST", _env("POF_LAPTOP_LAN", _env("POF_DESKTOP_LAN", "192.168.1.76"))) or "192.168.1.76"
DASHBOARD_URL = _env("POF_DASHBOARD_URL", f"http://{DASHBOARD_HOST}:{APP_PORT}") or f"http://{DASHBOARD_HOST}:{APP_PORT}"
PREFERRED_ROUTE_ORDER = tuple((_env("POF_ROUTE_ORDER", "direct,lan") or "direct,lan").replace(" ", "").split(","))
REQUEST_TIMEOUT_SECONDS = _env_float("POF_REQUEST_TIMEOUT_SECONDS", 1.5)

AUTH_ENABLED = _env_bool("POF_AUTH_ENABLED", False)
MASTER_TOKEN = _env("POF_MASTER_TOKEN")
CODEX_TOKEN = _env("POF_CODEX_TOKEN")

DATA_DIR = Path(_env("POF_DATA_DIR", str(BASE_DIR / "data")) or str(BASE_DIR / "data"))
SQLITE_PATH = Path(_env("POF_SQLITE_PATH", str(DATA_DIR / "pof2828.db")) or str(DATA_DIR / "pof2828.db"))
POSTGRES_DSN = _env("POF_POSTGRES_DSN")
POSTGRES_TARGETS = {
    "main": {
        "name": "PostgreSQL Main",
        "port": 28301,
        "dsn": _env("POF_POSTGRES_MAIN_DSN", POSTGRES_DSN),
        "role": "primary relational database",
    },
    "memory": {
        "name": "PostgreSQL Memory",
        "port": 28302,
        "dsn": _env("POF_POSTGRES_MEMORY_DSN"),
        "role": "memory, embeddings, and assistant working data",
    },
    "analytics": {
        "name": "PostgreSQL Analytics",
        "port": 28303,
        "dsn": _env("POF_POSTGRES_ANALYTICS_DSN"),
        "role": "reporting, event history, and metrics",
    },
}

SYNOLOGY_HOST = _env("POF_SYNOLOGY_HOST", _env("POF_NAS_LAN", "192.168.1.177"))
SYNOLOGY_PORT = _env_int("POF_SYNOLOGY_PORT", 5000)
SYNOLOGY_USERNAME = _env("POF_SYNOLOGY_USERNAME")
SYNOLOGY_PASSWORD = _env("POF_SYNOLOGY_PASSWORD")
SYNOLOGY_QUICKCONNECT_ID = _env("POF_SYNOLOGY_QUICKCONNECT_ID")
SYNOLOGY_SECURE = _env_bool("POF_SYNOLOGY_SECURE", False)
SYNOLOGY_CERT_VERIFY = _env_bool("POF_SYNOLOGY_CERT_VERIFY", False)
SYNOLOGY_DSM_VERSION = _env_int("POF_SYNOLOGY_DSM_VERSION", 7)


def port_range_for(port: int) -> dict[str, Any] | None:
    for port_range in PORT_RANGES:
        if port_range.contains(port):
            return asdict(port_range)
    return None


def service_catalog() -> list[dict[str, Any]]:
    return [{**spec.payload(), "range": port_range_for(spec.port)} for spec in SERVICE_SPECS]
