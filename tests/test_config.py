"""Tests for MooAId configuration system."""

import pytest
from pathlib import Path
import tempfile
import yaml

from mooaid.config import (
    Config,
    ConfigManager,
    ProviderConfig,
    OllamaConfig,
    DatabaseConfig,
    APIConfig,
    LoggingConfig,
    load_config,
    get_config,
)


class TestProviderConfig:
    """Tests for ProviderConfig model."""

    def test_default_values(self):
        """Test default values for provider config."""
        config = ProviderConfig()
        assert config.api_key == ""
        assert config.base_url == ""
        assert config.default_model == ""

    def test_custom_values(self):
        """Test custom values for provider config."""
        config = ProviderConfig(
            api_key="test-key",
            base_url="https://test.com",
            default_model="test-model",
        )
        assert config.api_key == "test-key"
        assert config.base_url == "https://test.com"
        assert config.default_model == "test-model"


class TestOllamaConfig:
    """Tests for OllamaConfig model."""

    def test_default_values(self):
        """Test default values for Ollama config."""
        config = OllamaConfig()
        assert config.host == "http://localhost:11434"
        assert config.model == "llama3"


class TestConfig:
    """Tests for main Config model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.provider == "openrouter"
        assert isinstance(config.openrouter, ProviderConfig)
        assert isinstance(config.ollama, OllamaConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.api, APIConfig)
        assert isinstance(config.logging, LoggingConfig)


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_singleton_pattern(self):
        """Test that ConfigManager is a singleton."""
        cm1 = ConfigManager()
        cm2 = ConfigManager()
        assert cm1 is cm2

    def test_load_nonexistent_config(self):
        """Test loading a non-existent config file."""
        config = ConfigManager.load("/nonexistent/path/config.yaml")
        assert isinstance(config, Config)
        assert config.provider == "openrouter"

    def test_load_custom_config(self):
        """Test loading a custom config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"provider": "ollama"}, f)
            temp_path = f.name

        try:
            config = ConfigManager.load(temp_path)
            assert config.provider == "ollama"
        finally:
            Path(temp_path).unlink()

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            config = Config()
            config.provider = "gemini"
            ConfigManager.save(config, temp_path)

            loaded = ConfigManager.load(temp_path)
            assert loaded.provider == "gemini"
        finally:
            Path(temp_path).unlink()


class TestConfigFunctions:
    """Tests for config helper functions."""

    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        assert isinstance(config, Config)

    def test_load_config(self):
        """Test load_config function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"provider": "openai"}, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.provider == "openai"
        finally:
            Path(temp_path).unlink()
