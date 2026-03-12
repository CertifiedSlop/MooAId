"""Core AI provider interface for MooAId."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationResult:
    """Result from AI generation."""

    content: str
    model: str
    provider: str
    usage: dict[str, Any] | None = None
    raw_response: Any | None = None


class AIProvider(ABC):
    """Abstract base class for AI providers.

    All AI providers must implement this interface.
    """

    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> GenerationResult:
        """Generate a response from the AI model.

        Args:
            prompt: The prompt to send to the AI model.

        Returns:
            GenerationResult: The result from the AI model.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Check if the provider is available and healthy.

        Returns:
            bool: True if healthy, False otherwise.
        """
        pass

    def get_name(self) -> str:
        """Get the provider name.

        Returns:
            str: The provider name.
        """
        return self.name
