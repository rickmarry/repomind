import json
import shutil
import subprocess
import sys
from typing import Callable

from repomind.providers.base import BaseProvider, Message, ProviderError

_RATE_LIMIT_PHRASES = ("rate limit", "too many requests", "429")
_ERROR_PHRASES = _RATE_LIMIT_PHRASES + ("credit", "quota", "exceeded", "usage limit")


class ClaudeCliProvider(BaseProvider):
    name = "claude_cli"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def complete(
        self,
        messages: list[Message],
        max_tokens: int,
        stream: bool = True,
        on_first_chunk: Callable | None = None,
    ) -> str:
        transcript = "\n\n".join(
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in messages
        )

        if stream:
            return self._stream_json(transcript, on_first_chunk=on_first_chunk)

        result = subprocess.run(
            ["claude", "-p", transcript],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        if result.returncode != 0:
            stderr_lower = result.stderr.lower()
            if any(phrase in stderr_lower for phrase in _RATE_LIMIT_PHRASES):
                raise ProviderError(f"claude CLI rate limited: {result.stderr.strip()}")
            raise ProviderError(f"claude CLI exit {result.returncode}: {result.stderr.strip()}")
        return self._check_plain_output(output)

    def _check_plain_output(self, output: str) -> str:
        """Raise ProviderError if output contains an error phrase, else return it."""
        output_lower = output.lower()
        if any(phrase in output_lower for phrase in _ERROR_PHRASES):
            if any(phrase in output_lower for phrase in _RATE_LIMIT_PHRASES):
                raise ProviderError(f"claude CLI rate limited: {output.strip()}")
            raise ProviderError(f"claude CLI error in output: {output.strip()}")
        return output

    def _stream_json(self, transcript: str, on_first_chunk: Callable | None = None) -> str:
        """Stream using --output-format stream-json for real incremental output.

        Each line from the CLI is a JSON event. We extract text from
        content_block_delta events and write immediately to stdout.
        On a result event with is_error=true we raise ProviderError.
        """
        proc = subprocess.Popen(
            ["claude", "-p", transcript, "--output-format", "stream-json", "--include-partial-messages"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        output_parts: list[str] = []
        assert proc.stdout is not None

        for raw_line in proc.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type")

            if event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        if on_first_chunk:
                            on_first_chunk()
                            on_first_chunk = None
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        output_parts.append(text)

            elif event_type == "result":
                is_error = event.get("is_error", False)
                if is_error:
                    result_text = event.get("result", "")
                    result_lower = result_text.lower()
                    if any(phrase in result_lower for phrase in _RATE_LIMIT_PHRASES):
                        raise ProviderError(f"claude CLI rate limited: {result_text.strip()}")
                    raise ProviderError(f"claude CLI error: {result_text.strip()}")

        proc.wait()

        if proc.returncode != 0 and not output_parts:
            stderr_out = proc.stderr.read() if proc.stderr else ""
            stderr_lower = stderr_out.lower()
            if any(phrase in stderr_lower for phrase in _RATE_LIMIT_PHRASES):
                raise ProviderError(f"claude CLI rate limited: {stderr_out.strip()}")
            raise ProviderError(f"claude CLI exit {proc.returncode}: {stderr_out.strip()}")

        return "".join(output_parts)
