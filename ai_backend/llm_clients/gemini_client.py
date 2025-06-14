import asyncio

try:
    from google.generativeai import generate_text
except ImportError:  # pragma: no cover - if package not installed
    generate_text = None


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model

    async def generate(self, question: str, context: str) -> str:
        if generate_text is None:
            raise RuntimeError("google-generativeai not installed")
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: generate_text(
                model=self.model, prompt=prompt, api_key=self.api_key
            ),
        )
        return response.text
