import os
import sys

from repomind.providers.base import BaseProvider, Message, ProviderError


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self):
        self._client = None

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        return self._client

    def complete(self, messages: list[Message], max_tokens: int, stream: bool = True) -> str:
        try:
            sdk_messages = [{"role": m.role, "content": m.content} for m in messages]
            if stream:
                output = []
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=max_tokens,
                    messages=sdk_messages,
                    stream=True,
                )
                for chunk in response:
                    text = chunk.choices[0].delta.content or ""
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    output.append(text)
                return "".join(output)
            else:
                res = self.client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=max_tokens,
                    messages=sdk_messages,
                )
                return res.choices[0].message.content
        except Exception as e:
            raise ProviderError(f"OpenAI error: {e}") from e
