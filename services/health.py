from .simple import StaticService


class HealthDashboardService(StaticService):
    def __init__(self) -> None:
        super().__init__("Health dashboard", 28290, "C")
