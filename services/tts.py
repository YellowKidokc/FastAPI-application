from .simple import StaticService


class TTSService(StaticService):
    def __init__(self) -> None:
        super().__init__("TTS", 28285, "T")
