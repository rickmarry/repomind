import os
import pty
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
            return self._stream_via_pty(["claude", "-p", transcript], on_first_chunk=on_first_chunk)

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
        return self._check_output(output)

    def _check_output(self, output: str) -> str:
        """Raise ProviderError if output contains an error phrase, else return it."""
        output_lower = output.lower()
        if any(phrase in output_lower for phrase in _ERROR_PHRASES):
            if any(phrase in output_lower for phrase in _RATE_LIMIT_PHRASES):
                raise ProviderError(f"claude CLI rate limited: {output.strip()}")
            raise ProviderError(f"claude CLI error in output: {output.strip()}")
        return output

    def _stream_via_pty(self, cmd: list[str], on_first_chunk: Callable | None = None) -> str:
        """Run cmd under a PTY, buffer all output, check for errors before writing to stdout.

        Since `claude -p` does not flush incrementally, buffering has no UX cost and
        prevents error text from leaking to stdout before the fallback chain can react.
        """
        master_fd, slave_fd = pty.openpty()
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
            )
            os.close(slave_fd)
            slave_fd = -1

            chunks: list[str] = []
            while True:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    # master end closed — child exited
                    break
                if not data:
                    break
                chunks.append(data.decode("utf-8", errors="replace"))

            proc.wait()
        finally:
            os.close(master_fd)
            if slave_fd != -1:
                os.close(slave_fd)

        output = "".join(chunks)
        # Check for errors before writing anything — this prevents error text from
        # bleeding into stdout when we fall back to another provider.
        output = self._check_output(output)
        if on_first_chunk:
            on_first_chunk()
        sys.stdout.write(output)
        sys.stdout.flush()
        return output
