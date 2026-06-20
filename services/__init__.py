from .clipboard import ClipboardService
from .comms import CommsService
from .fis import FISService
from .health import HealthDashboardService
from .lossless import LosslessService
from .nlp import NLPService
from .postgres import PostgresService
from .synology import SynologyService
from .tts import TTSService

SERVICES = [
    SynologyService(),
    PostgresService("main"),
    PostgresService("memory"),
    PostgresService("analytics"),
    FISService(),
    NLPService(),
    TTSService(),
    LosslessService(),
    CommsService(),
    ClipboardService(),
    HealthDashboardService(),
]
