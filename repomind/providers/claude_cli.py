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
            proc = subprocess.Popen(
                ["claude", "-p", transcript],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            lines = []
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                lines.append(line)
            proc.wait()
            output = "".join(lines)
            stderr = proc.stderr.read()
            returncode = proc.returncode
        else:
            result = subprocess.run(
                ["claude", "-p", transcript],
                capture_output=True,
                text=True,
            )
            output = result.stdout
            stderr = result.stderr
            returncode = result.returncode

        # Claude CLI sometimes exits 0 but writes an error to stdout
        if returncode == 0:
            output_lower = output.lower()
            if any(phrase in output_lower for phrase in _ERROR_PHRASES):
                if any(phrase in output_lower for phrase in _RATE_LIMIT_PHRASES):
                    raise ProviderError(f"claude CLI rate limited: {output.strip()}")
                raise ProviderError(f"claude CLI error in output: {output.strip()}")
            return output

        stderr_lower = stderr.lower()
        if any(phrase in stderr_lower for phrase in _RATE_LIMIT_PHRASES):
            raise ProviderError(f"claude CLI rate limited: {stderr.strip()}")
        raise ProviderError(f"claude CLI exit {returncode}: {stderr.strip()}")
