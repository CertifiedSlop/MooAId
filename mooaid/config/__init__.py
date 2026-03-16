"""Configuration module for MooAId."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Base provider configuration."""

    api_key: str = ""
    base_url: str = ""
    default_model: str = ""


class OllamaConfig(BaseModel):
    """Ollama-specific configuration."""

    host: str = "http://localhost:11434"
    model: str = "llama3"


class DatabaseConfig(BaseModel):
    """Database configuration."""

    path: str = "./mooaid.db"


class APIConfig(BaseModel):
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Config(BaseModel):
    """Main configuration model for MooAId."""

    provider: str = "openrouter"
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ConfigManager:
    """Manages loading and accessing configuration."""

    _instance: "ConfigManager | None" = None
    _config: Config | None = None

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern for config manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the config manager."""
        if self._config is None:
            self._config = None  # Will be loaded on first access

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> Config:
        """Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file. Defaults to ./config.yaml

        Returns:
            Config: The loaded configuration object.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            # Return default config if file doesn't exist
            return Config()

        with open(config_path, "r") as f:
            raw_config: dict[str, Any] = yaml.safe_load(f) or {}

        # Parse nested configurations
        config_data: dict[str, Any] = {
            "provider": raw_config.get("provider", "openrouter"),
        }

        if "openrouter" in raw_config:
            config_data["openrouter"] = ProviderConfig(**raw_config["openrouter"])

        if "ollama" in raw_config:
            config_data["ollama"] = OllamaConfig(**raw_config["ollama"])

        if "openai" in raw_config:
            config_data["openai"] = ProviderConfig(**raw_config["openai"])

        if "gemini" in raw_config:
            config_data["gemini"] = ProviderConfig(**raw_config["gemini"])

        if "database" in raw_config:
            config_data["database"] = DatabaseConfig(**raw_config["database"])

        if "api" in raw_config:
            config_data["api"] = APIConfig(**raw_config["api"])

        if "logging" in raw_config:
            config_data["logging"] = LoggingConfig(**raw_config["logging"])

        config = Config(**config_data)

        # Override with environment variables (for Docker deployment)
        # Only use env vars if they are not empty
        if env_provider := os.environ.get("MOOAID_PROVIDER"):
            config.provider = env_provider
        if env_db_path := os.environ.get("MOOAID_DB_PATH"):
            config.database.path = env_db_path
        if env_api_host := os.environ.get("MOOAID_HOST"):
            config.api.host = env_api_host
        if env_api_port := os.environ.get("MOOAID_PORT"):
            config.api.port = int(env_api_port)
        # Only override API keys if env var is set and not empty
        if (env_openrouter_key := os.environ.get("OPENROUTER_API_KEY")) and env_openrouter_key.strip():
            config.openrouter.api_key = env_openrouter_key
        if (env_openai_key := os.environ.get("OPENAI_API_KEY")) and env_openai_key.strip():
            config.openai.api_key = env_openai_key
        if (env_gemini_key := os.environ.get("GEMINI_API_KEY")) and env_gemini_key.strip():
            config.gemini.api_key = env_gemini_key
        if (env_ollama_host := os.environ.get("OLLAMA_HOST")) and env_ollama_host.strip():
            config.ollama.host = env_ollama_host

        cls._config = config
        return cls._config

    @classmethod
    def get(cls) -> Config:
        """Get the current configuration.

        Returns:
            Config: The current configuration object.
        """
        if cls._config is None:
            return cls.load()
        return cls._config

    @classmethod
    def get_provider_config(cls, provider_name: str | None = None) -> ProviderConfig | OllamaConfig:
        """Get configuration for a specific provider.

        Args:
            provider_name: Name of the provider. Defaults to current configured provider.

        Returns:
            ProviderConfig | OllamaConfig: The provider configuration.
        """
        config = cls.get()
        provider = provider_name or config.provider

        provider_configs: dict[str, ProviderConfig | OllamaConfig] = {
            "openrouter": config.openrouter,
            "ollama": config.ollama,
            "openai": config.openai,
            "gemini": config.gemini,
        }

        return provider_configs.get(provider, config.openrouter)

    @classmethod
    def save(cls, config: Config, config_path: str | Path | None = None) -> None:
        """Save configuration to YAML file.

        Args:
            config: The configuration to save.
            config_path: Path to the configuration file. Defaults to ./config.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)

        config_dict = config.model_dump()

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        cls._config = config


def get_config() -> Config:
    """Get the current configuration.

    Returns:
        Config: The current configuration object.
    """
    return ConfigManager.get()


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from a file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Config: The loaded configuration object.
    """
    return ConfigManager.load(config_path)
