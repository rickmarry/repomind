from abc import ABC, abstractmethod
from dataclasses import dataclass


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
    def complete(self, messages: list[Message], max_tokens: int) -> str:
        """
        Send messages and return the text response.
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
