from .simple import StaticService


class FISService(StaticService):
    def __init__(self) -> None:
        super().__init__("FIS", 28282, "M")
