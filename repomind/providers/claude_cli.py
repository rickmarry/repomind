import shutil
import subprocess
import sys

from repomind.providers.base import BaseProvider, Message, ProviderError

_RATE_LIMIT_PHRASES = ("rate limit", "too many requests", "429")


class ClaudeCliProvider(BaseProvider):
    name = "claude_cli"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def complete(self, messages: list[Message], max_tokens: int, stream: bool = True) -> str:
        transcript = "\n\n".join(
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in messages
        )

        process = subprocess.Popen(
            ["claude", "-p", transcript],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        chunks = []
        for chunk in process.stdout:
            chunks.append(chunk)
            if stream:
                sys.stdout.write(chunk)
                sys.stdout.flush()

        process.wait()

        if process.returncode != 0:
            stderr = process.stderr.read()
            stderr_lower = stderr.lower()
            if any(phrase in stderr_lower for phrase in _RATE_LIMIT_PHRASES):
                raise ProviderError(f"claude CLI rate limited: {stderr.strip()}")
            raise ProviderError(f"claude CLI exit {process.returncode}: {stderr.strip()}")

        return "".join(chunks)
