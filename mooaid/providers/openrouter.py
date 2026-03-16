"""OpenRouter AI provider implementation."""

import httpx
from pydantic import BaseModel

from mooaid.config import Config, ProviderConfig
from mooaid.core import AIProvider, GenerationResult
from mooaid.core.provider_factory import register_provider


class OpenRouterConfig(BaseModel):
    """OpenRouter configuration model."""

    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-3-haiku"


class OpenRouterProvider(AIProvider):
    """OpenRouter AI provider."""

    name = "openrouter"

    def __init__(self, config: Config) -> None:
        """Initialize the OpenRouter provider.

        Args:
            config: The application configuration.
        """
        self.config = OpenRouterConfig(
            api_key=config.openrouter.api_key,
            base_url=config.openrouter.base_url or "https://openrouter.ai/api/v1",
            default_model=config.openrouter.default_model
            or "anthropic/claude-3-haiku",
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
                    # OpenRouter specific headers
                    "HTTP-Referer": "https://github.com/CertifiedSlop/MooAId",
                    "X-Title": "MooAId",
                },
                timeout=60.0,
            )
        return self._client

    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """Generate a response from OpenRouter.

        Args:
            prompt: The prompt to send.
            model: Optional model override.

        Returns:
            GenerationResult: The generation result.

        Raises:
            RuntimeError: If API key is not set or request fails.
        """
        if not self.config.api_key:
            raise RuntimeError("OpenRouter API key is not configured")

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
            raise RuntimeError(f"OpenRouter API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenRouter request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Invalid OpenRouter response: {e}") from e

    async def check_health(self) -> bool:
        """Check if OpenRouter is available.

        Returns:
            bool: True if healthy.
        """
        if not self.config.api_key:
            return False

        try:
            client = await self._get_client()
            # Try to get models endpoint
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def get_models(self) -> list[dict[str, str]]:
        """Get available models from OpenRouter.

        Returns:
            list: List of available models with id and name.
        """
        if not self.config.api_key:
            # Return default models if no API key
            return [
                {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku"},
                {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"},
                {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
                {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "openai/gpt-4o", "name": "GPT-4o"},
                {"id": "meta-llama/llama-3-70b-instruct", "name": "Llama 3 70B"},
                {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5"},
                {"id": "mistralai/mistral-large", "name": "Mistral Large"},
            ]

        try:
            client = await self._get_client()
            # OpenRouter uses /models endpoint
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                model_name = model.get("name", model.get("id", ""))
                # Only include text models for now
                if model_id:
                    models.append({
                        "id": model_id,
                        "name": model_name,
                    })
            return models
        except Exception as e:
            # Return default models if API call fails
            return [
                {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku"},
                {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"},
                {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
                {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "openai/gpt-4o", "name": "GPT-4o"},
                {"id": "meta-llama/llama-3-70b-instruct", "name": "Llama 3 70B"},
                {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5"},
                {"id": "mistralai/mistral-large", "name": "Mistral Large"},
            ]

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Register the provider
register_provider("openrouter", OpenRouterProvider)
