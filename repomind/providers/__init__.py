import sys
import threading

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


def _run_spinner(done: threading.Event) -> None:
    """Write an animated spinner to stderr until done is set, then clear the line."""
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while not done.wait(0.08):
        sys.stderr.write(f"\r\x1b[2m{frames[i % len(frames)]} thinking...\x1b[0m")
        sys.stderr.flush()
        i += 1
    # Clear spinner line so content starts from a clean position
    sys.stderr.write("\r\x1b[2K")
    sys.stderr.flush()


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
                sys.stderr.write(f"\x1b[2mvia {name}\x1b[0m\n")
                sys.stderr.flush()

                done = threading.Event()
                spinner_thread = threading.Thread(target=_run_spinner, args=(done,), daemon=True)
                spinner_thread.start()

                def on_first_chunk(_done=done, _t=spinner_thread):
                    """Stop spinner and wait for it to clear before first content writes."""
                    _done.set()
                    _t.join(timeout=0.5)

                try:
                    return provider.complete(messages, max_tokens, stream=True, on_first_chunk=on_first_chunk)
                finally:
                    # Ensure spinner stops even if provider raised without calling on_first_chunk
                    done.set()
                    spinner_thread.join(timeout=1)
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
                sys.stderr.write(f"\x1b[33m{name} {reason}, trying next provider...\x1b[0m\n")
                sys.stderr.flush()

    raise RuntimeError(
        "All providers exhausted.\n" + "\n".join(f"  - {e}" for e in errors)
    )
