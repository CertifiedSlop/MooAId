"""Google Gemini AI provider implementation."""

import httpx
from pydantic import BaseModel

from mooaid.config import Config, ProviderConfig
from mooaid.core import AIProvider, GenerationResult
from mooaid.core.provider_factory import register_provider


class GeminiConfig(BaseModel):
    """Google Gemini configuration model."""

    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    default_model: str = "gemini-pro"


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""

    name = "gemini"

    def __init__(self, config: Config) -> None:
        """Initialize the Gemini provider.

        Args:
            config: The application configuration.
        """
        self.config = GeminiConfig(
            api_key=config.gemini.api_key,
            base_url=config.gemini.base_url
            or "https://generativelanguage.googleapis.com/v1beta",
            default_model=config.gemini.default_model or "gemini-pro",
        )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={"Content-Type": "application/json"},
                timeout=60.0,
            )
        return self._client

    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """Generate a response from Gemini.

        Args:
            prompt: The prompt to send.
            model: Optional model override.

        Returns:
            GenerationResult: The generation result.

        Raises:
            RuntimeError: If API key is not set or request fails.
        """
        if not self.config.api_key:
            raise RuntimeError("Google Gemini API key is not configured")

        client = await self._get_client()
        model_name = model or self.config.default_model

        try:
            # Gemini API endpoint format
            endpoint = f"/models/{model_name}:generateContent"
            response = await client.post(
                endpoint,
                params={"key": self.config.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract content from Gemini response format
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No response from Gemini")

            content = candidates[0]["content"]["parts"][0]["text"]

            # Extract usage metadata if available
            usage_metadata = data.get("usageMetadata")
            usage = None
            if usage_metadata:
                usage = {
                    "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                    "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                    "total_tokens": usage_metadata.get("totalTokenCount", 0),
                }

            return GenerationResult(
                content=content,
                model=model_name,
                provider=self.name,
                usage=usage,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Gemini API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Gemini request failed: {e}") from e
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"Invalid Gemini response: {e}") from e

    async def check_health(self) -> bool:
        """Check if Gemini is available.

        Returns:
            bool: True if healthy.
        """
        if not self.config.api_key:
            return False

        try:
            client = await self._get_client()
            # Try to get model info
            model_name = self.config.default_model
            response = await client.get(
                f"/models/{model_name}", params={"key": self.config.api_key}
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Register the provider
register_provider("gemini", GeminiProvider)
