"""Provider factory for creating AI provider instances."""

from typing import Any

from mooaid.config import Config, get_config
from mooaid.core import AIProvider


class ProviderFactory:
    """Factory for creating AI provider instances."""

    _providers: dict[str, type[AIProvider]] = {}
    _instances: dict[str, AIProvider] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[AIProvider]) -> None:
        """Register a provider class.

        Args:
            name: The provider name.
            provider_class: The provider class to register.
        """
        cls._providers[name.lower()] = provider_class

    @classmethod
    def create(
        cls, provider_name: str | None = None, config: Config | None = None
    ) -> AIProvider:
        """Create a provider instance.

        Args:
            provider_name: Optional provider name. Defaults to configured provider.
            config: Optional config. Defaults to loaded config.

        Returns:
            AIProvider: The provider instance.

        Raises:
            ValueError: If provider is not found or not registered.
        """
        if config is None:
            config = get_config()

        provider_name = (provider_name or config.provider).lower()

        # Return cached instance if available
        if provider_name in cls._instances:
            return cls._instances[provider_name]

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not found. Available: {available}"
            )

        provider_class = cls._providers[provider_name]
        instance = provider_class(config)
        cls._instances[provider_name] = instance

        return instance

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names.

        Returns:
            list[str]: List of provider names.
        """
        return list(cls._providers.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached provider instances."""
        cls._instances.clear()


def get_provider(
    provider_name: str | None = None, config: Config | None = None
) -> AIProvider:
    """Get a provider instance.

    Args:
        provider_name: Optional provider name.
        config: Optional config.

    Returns:
        AIProvider: The provider instance.
    """
    return ProviderFactory.create(provider_name, config)


def register_provider(name: str, provider_class: type[AIProvider]) -> None:
    """Register a provider class.

    Args:
        name: The provider name.
        provider_class: The provider class to register.
    """
    ProviderFactory.register(name, provider_class)
