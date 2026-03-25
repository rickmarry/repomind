import shutil
import subprocess

from repomind.providers.base import BaseProvider, Message, ProviderError

_RATE_LIMIT_PHRASES = ("rate limit", "too many requests", "429")


class ClaudeCliProvider(BaseProvider):
    name = "claude_cli"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def complete(self, messages: list[Message], max_tokens: int) -> str:
        # Build a transcript so the full history reaches the CLI
        transcript = "\n\n".join(
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in messages
        )

        result = subprocess.run(
            ["claude", "-p", transcript],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return result.stdout

        stderr_lower = result.stderr.lower()
        if any(phrase in stderr_lower for phrase in _RATE_LIMIT_PHRASES):
            raise ProviderError(f"claude CLI rate limited: {result.stderr.strip()}")

        raise ProviderError(f"claude CLI exit {result.returncode}: {result.stderr.strip()}")
