from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class Message:
    role: str    # "user" or "assistant"
    content: str


class ProviderError(Exception):
    """Raised when a provider fails in a way that should trigger chain fallback."""
    pass


class BaseProvider(ABC):
    name: str  # class-level identifier, e.g. "claude_cli", "anthropic_api"

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        max_tokens: int,
        stream: bool = True,
        on_first_chunk: Callable | None = None,
    ) -> str:
        """
        Send messages and return the text response.
        When stream=True, print chunks to stdout as they arrive.
        Call on_first_chunk() (if provided) exactly once, before writing the
        first chunk — this lets the caller stop a spinner cleanly before output.
        Raise ProviderError on failures that should trigger fallback.
        Raise other exceptions for hard failures that should halt the chain.
        """
        ...

    def is_available(self) -> bool:
        """
        Pre-flight check. Return False to silently skip this provider.
        Subclasses override to check env vars, binary presence, etc.
        """
        return True
