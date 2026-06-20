from __future__ import annotations

from pathlib import Path

PORTS = {
    28280: {"name": "Master API", "channel": "chi"},
    28281: {"name": "PostgreSQL proxy", "channel": "G"},
    28282: {"name": "FIS", "channel": "M"},
    28283: {"name": "NLP Pipeline", "channel": "E"},
    28284: {"name": "Dedup daemon", "channel": "S"},
    28285: {"name": "TTS", "channel": "T"},
    28286: {"name": "Lossless Compression", "channel": "K"},
    28287: {"name": "Comms Hub", "channel": "R"},
    28288: {"name": "Clipboard", "channel": "Q"},
    28289: {"name": "Cross-service bridge", "channel": "F"},
    28290: {"name": "Health dashboard", "channel": "C"},
}

HOSTS = {
    "desktop": {"lan": "192.168.1.76", "direct": "192.168.2.51"},
    "nas": {"lan": "192.168.1.177", "direct": "192.168.2.50"},
    "laptop": {"lan": None},
}

SERVICE_PORTS = tuple(PORTS.keys())
PREFERRED_ROUTE_ORDER = ("direct", "lan")
REQUEST_TIMEOUT_SECONDS = 1.5

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SQLITE_PATH = DATA_DIR / "pof2828.db"
POSTGRES_DSN = "postgresql://postgres:postgres@192.168.2.50:5432/pof2828"
