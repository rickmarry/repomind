from rich import print

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
                print(f"[dim]via {name}[/dim]")
            return provider.complete(messages, max_tokens, stream=stream)
        except ProviderError as e:
            errors.append(f"{name}: {e}")
            has_next = any(
                REGISTRY.get(n) and REGISTRY[n]().is_available()
                for n in providers_to_try[i + 1:]
            )
            if has_next:
                print(f"[yellow]{name} unavailable, trying next provider...[/yellow]")

    raise RuntimeError(
        "All providers exhausted.\n" + "\n".join(f"  - {e}" for e in errors)
    )
