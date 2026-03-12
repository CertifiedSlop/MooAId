"""OpenAI ChatGPT provider implementation."""

import httpx
from pydantic import BaseModel

from mooaid.config import Config, ProviderConfig
from mooaid.core import AIProvider, GenerationResult
from mooaid.core.provider_factory import register_provider


class OpenAIConfig(BaseModel):
    """OpenAI configuration model."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-3.5-turbo"


class OpenAIProvider(AIProvider):
    """OpenAI ChatGPT provider."""

    name = "openai"

    def __init__(self, config: Config) -> None:
        """Initialize the OpenAI provider.

        Args:
            config: The application configuration.
        """
        self.config = OpenAIConfig(
            api_key=config.openai.api_key,
            base_url=config.openai.base_url or "https://api.openai.com/v1",
            default_model=config.openai.default_model or "gpt-3.5-turbo",
        )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """Generate a response from OpenAI.

        Args:
            prompt: The prompt to send.
            model: Optional model override.

        Returns:
            GenerationResult: The generation result.

        Raises:
            RuntimeError: If API key is not set or request fails.
        """
        if not self.config.api_key:
            raise RuntimeError("OpenAI API key is not configured")

        client = await self._get_client()
        model_name = model or self.config.default_model

        try:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            return GenerationResult(
                content=content,
                model=model_name,
                provider=self.name,
                usage=usage,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Invalid OpenAI response: {e}") from e

    async def check_health(self) -> bool:
        """Check if OpenAI is available.

        Returns:
            bool: True if healthy.
        """
        if not self.config.api_key:
            return False

        try:
            client = await self._get_client()
            # Try to list models
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Register the provider
register_provider("openai", OpenAIProvider)
