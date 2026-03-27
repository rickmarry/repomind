import sys

from rich import print
from rich.console import Console

from repomind.providers.base import BaseProvider, Message, ProviderError
from repomind.providers.claude_cli import ClaudeCliProvider
from repomind.providers.anthropic_api import AnthropicApiProvider
from repomind.providers.openai import OpenAIProvider
from repomind.providers.gemini import GeminiProvider

REGISTRY: dict[str, type[BaseProvider]] = {
    "claude_cli": ClaudeCliProvider,
    "anthropic_api": AnthropicApiProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}

DEFAULT_CHAIN = ["claude_cli", "anthropic_api", "openai", "gemini"]

_console = Console()


def call_chain(
    messages: list[Message],
    max_tokens: int,
    chain: list[str],
    via: str | None = None,
    stream: bool = True,
) -> str:
    """
    Walk the provider chain and return the first successful response.

    If `via` is set, only that provider is attempted (one-shot override).
    Providers where is_available() returns False are silently skipped.
    Raises RuntimeError if all providers fail or are unavailable.
    """
    providers_to_try = [via] if via else chain

    errors = []
    for i, name in enumerate(providers_to_try):
        cls = REGISTRY.get(name)
        if cls is None:
            errors.append(f"{name}: unknown provider")
            continue

        provider = cls()
        if not provider.is_available():
            continue

        try:
            if stream:
                # Print provider name immediately, bypassing rich buffering
                sys.stdout.write(f"\x1b[2mvia {name}\x1b[0m\n")
                sys.stdout.flush()

                # Spinner runs until the first chunk arrives
                status = _console.status("[dim]thinking...[/dim]", spinner="dots")
                status.start()
                _orig_write = sys.stdout.write
                _stopped = [False]

                def _intercept(text, _orig=_orig_write, _status=status, _stopped=_stopped):
                    if not _stopped[0]:
                        _stopped[0] = True
                        _status.stop()
                        sys.stdout.write = _orig
                    return _orig(text)

                sys.stdout.write = _intercept
                try:
                    return provider.complete(messages, max_tokens, stream=True)
                finally:
                    # Always clean up — covers errors and empty responses
                    if not _stopped[0]:
                        status.stop()
                    sys.stdout.write = _orig_write
            else:
                return provider.complete(messages, max_tokens, stream=False)
        except ProviderError as e:
            errors.append(f"{name}: {e}")
            reason = "rate limited" if "rate limit" in str(e).lower() else "unavailable"
            has_next = any(
                REGISTRY.get(n) and REGISTRY[n]().is_available()
                for n in providers_to_try[i + 1:]
            )
            if has_next:
                print(f"[yellow]{name} {reason}, trying next provider...[/yellow]")

    raise RuntimeError(
        "All providers exhausted.\n" + "\n".join(f"  - {e}" for e in errors)
    )
