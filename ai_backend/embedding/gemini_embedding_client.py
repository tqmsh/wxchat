from typing import List
import asyncio

try:
    from google.generativeai import embedding
except ImportError:  # pragma: no cover - if package not installed
    embedding = None


class GeminiEmbeddingClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if embedding is None:
            raise RuntimeError("google-generativeai not installed")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: embedding.embed_many(texts, api_key=self.api_key))

    async def embed_query(self, text: str) -> List[float]:
        if embedding is None:
            raise RuntimeError("google-generativeai not installed")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: embedding.embed(text, api_key=self.api_key))
        return result
