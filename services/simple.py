from .base import ServiceBase


class StaticService(ServiceBase):
    def __init__(self, name: str, port: int, channel: str) -> None:
        self.name = name
        self.port = port
        self.channel = channel
