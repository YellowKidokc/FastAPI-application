from .simple import StaticService


class NLPService(StaticService):
    def __init__(self) -> None:
        super().__init__("NLP Pipeline", 28283, "E")
