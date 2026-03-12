"""Ollama local AI provider implementation."""

import httpx
from pydantic import BaseModel

from mooaid.config import Config, OllamaConfig
from mooaid.core import AIProvider, GenerationResult
from mooaid.core.provider_factory import register_provider


class OllamaProvider(AIProvider):
    """Ollama local AI provider."""

    name = "ollama"

    def __init__(self, config: Config) -> None:
        """Initialize the Ollama provider.

        Args:
            config: The application configuration.
        """
        self.config = OllamaConfig(
            host=config.ollama.host or "http://localhost:11434",
            model=config.ollama.model or "llama3",
        )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.host,
                headers={"Content-Type": "application/json"},
                timeout=120.0,  # Local models may take longer
            )
        return self._client

    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """Generate a response from Ollama.

        Args:
            prompt: The prompt to send.
            model: Optional model override.

        Returns:
            GenerationResult: The generation result.

        Raises:
            RuntimeError: If request fails.
        """
        client = await self._get_client()
        model_name = model or self.config.model

        try:
            response = await client.post(
                "/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("response", "")

            # Ollama doesn't provide token usage in the same format
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }

            return GenerationResult(
                content=content,
                model=model_name,
                provider=self.name,
                usage=usage,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Ollama request failed: {e}") from e
        except (KeyError, TypeError) as e:
            raise RuntimeError(f"Invalid Ollama response: {e}") from e

    async def check_health(self) -> bool:
        """Check if Ollama is available.

        Returns:
            bool: True if healthy.
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available Ollama models.

        Returns:
            list[str]: List of model names.
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Register the provider
register_provider("ollama", OllamaProvider)
