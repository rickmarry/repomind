import os

from repomind.providers.base import BaseProvider, Message, ProviderError


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self):
        self._client = None

    def is_available(self) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY"))

    @property
    def client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            self._client = genai.GenerativeModel("gemini-1.5-pro")
        return self._client

    def complete(self, messages: list[Message], max_tokens: int) -> str:
        try:
            # Gemini takes a single string; build a labelled transcript
            transcript = "\n\n".join(
                f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
                for m in messages
            )
            response = self.client.generate_content(transcript)
            return response.text
        except Exception as e:
            raise ProviderError(f"Gemini error: {e}") from e
