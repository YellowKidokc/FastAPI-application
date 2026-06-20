import zlib

from fastapi import FastAPI
from pydantic import BaseModel

from .simple import StaticService


class CompressionRequest(BaseModel):
    content: str


class LosslessService(StaticService):
    def __init__(self) -> None:
        super().__init__("Lossless Compression", 28286, "K")

    def compress(self, content: str) -> str:
        return zlib.compress(content.encode()).hex()

    def register_routes(self, app: FastAPI) -> None:
        super().register_routes(app)

        @app.post("/api/lossless/compress", tags=[self.name])
        async def compress(payload: CompressionRequest) -> dict[str, str]:
            return {"compressed": self.compress(payload.content)}
