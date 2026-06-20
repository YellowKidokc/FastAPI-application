from .clipboard import ClipboardService
from .comms import CommsService
from .fis import FISService
from .health import HealthDashboardService
from .lossless import LosslessService
from .nlp import NLPService
from .tts import TTSService

SERVICES = [
    FISService(),
    NLPService(),
    TTSService(),
    LosslessService(),
    CommsService(),
    ClipboardService(),
    HealthDashboardService(),
]
