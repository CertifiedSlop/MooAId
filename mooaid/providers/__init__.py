"""Providers package for MooAId."""

# Import all providers to ensure they are registered
from mooaid.providers.gemini import GeminiProvider
from mooaid.providers.ollama import OllamaProvider
from mooaid.providers.openai import OpenAIProvider
from mooaid.providers.openrouter import OpenRouterProvider

__all__ = [
    "OpenRouterProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "GeminiProvider",
]
