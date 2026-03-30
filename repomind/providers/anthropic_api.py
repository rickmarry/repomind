import os
import sys
from typing import Callable

from repomind.providers.base import BaseProvider, Message, ProviderError

_CREDIT_PHRASES = ("credit", "quota")


class AnthropicApiProvider(BaseProvider):
    name = "anthropic_api"

    def __init__(self):
        self._client = None

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    @property
    def client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        return self._client

    def complete(
        self,
        messages: list[Message],
        max_tokens: int,
        stream: bool = True,
        on_first_chunk: Callable | None = None,
    ) -> str:
        import anthropic as anthropic_lib

        sdk_messages = [{"role": m.role, "content": m.content} for m in messages]
        model = self._select_model(messages[-1].content)

        try:
            if stream:
                output = []
                with self.client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    messages=sdk_messages,
                ) as s:
                    for chunk in s.text_stream:
                        if on_first_chunk:
                            on_first_chunk()
                            on_first_chunk = None
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                        output.append(chunk)
                return "".join(output)
            else:
                res = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=sdk_messages,
                )
                return res.content[0].text
        except (anthropic_lib.RateLimitError, anthropic_lib.APIStatusError) as e:
            raise ProviderError(f"Anthropic API error: {e}") from e

    def _select_model(self, prompt: str) -> str:
        heavy = ("refactor", "design", "optimize", "architecture")
        if any(k in prompt.lower() for k in heavy):
            return "claude-3-5-sonnet-20240620"
        return "claude-3-haiku-20240307"
