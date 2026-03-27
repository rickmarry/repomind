import os
import pty
import shutil
import subprocess
import sys

from repomind.providers.base import BaseProvider, Message, ProviderError

_RATE_LIMIT_PHRASES = ("rate limit", "too many requests", "429")
_ERROR_PHRASES = _RATE_LIMIT_PHRASES + ("credit", "quota", "exceeded", "usage limit")


class ClaudeCliProvider(BaseProvider):
    name = "claude_cli"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def complete(self, messages: list[Message], max_tokens: int, stream: bool = True) -> str:
        transcript = "\n\n".join(
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in messages
        )

        if stream:
            output = self._stream_via_pty(["claude", "-p", transcript])
        else:
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

        # Claude CLI sometimes exits 0 but writes an error to stdout
        output_lower = output.lower()
        if any(phrase in output_lower for phrase in _ERROR_PHRASES):
            if any(phrase in output_lower for phrase in _RATE_LIMIT_PHRASES):
                raise ProviderError(f"claude CLI rate limited: {output.strip()}")
            raise ProviderError(f"claude CLI error in output: {output.strip()}")
        return output

    def _stream_via_pty(self, cmd: list[str]) -> str:
        """Run cmd under a PTY so the subprocess flushes output incrementally."""
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
                text = data.decode("utf-8", errors="replace")
                sys.stdout.write(text)
                sys.stdout.flush()
                chunks.append(text)

            proc.wait()
        finally:
            os.close(master_fd)
            if slave_fd != -1:
                os.close(slave_fd)

        return "".join(chunks)
