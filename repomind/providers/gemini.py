import os
import sys
from typing import Callable

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

    def complete(
        self,
        messages: list[Message],
        max_tokens: int,
        stream: bool = True,
        on_first_chunk: Callable | None = None,
    ) -> str:
        try:
            transcript = "\n\n".join(
                f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
                for m in messages
            )
            if stream:
                output = []
                response = self.client.generate_content(transcript, stream=True)
                for chunk in response:
                    text = chunk.text
                    if on_first_chunk:
                        on_first_chunk()
                        on_first_chunk = None
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    output.append(text)
                return "".join(output)
            else:
                response = self.client.generate_content(transcript)
                return response.text
        except Exception as e:
            raise ProviderError(f"Gemini error: {e}") from e
