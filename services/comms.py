from .simple import StaticService


class CommsService(StaticService):
    def __init__(self) -> None:
        super().__init__("Comms Hub", 28287, "R")
