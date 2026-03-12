"""Utility functions for MooAId."""

import logging
from pathlib import Path

from mooaid.config import Config, get_config


def setup_logging(config: Config | None = None) -> logging.Logger:
    """Set up logging configuration.

    Args:
        config: Optional configuration. Uses default if not provided.

    Returns:
        logging.Logger: The configured logger.
    """
    if config is None:
        config = get_config()

    log_config = config.logging

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_config.level.upper(), logging.INFO),
        format=log_config.format,
    )

    logger = logging.getLogger("mooaid")
    logger.setLevel(getattr(logging, log_config.level.upper(), logging.INFO))

    return logger


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path: The project root path.
    """
    return Path(__file__).parent.parent.parent


def ensure_config_exists() -> None:
    """Ensure the config file exists, create default if not."""
    config_path = get_project_root() / "config.yaml"

    if not config_path.exists():
        default_config = """# MooAId Configuration
provider: openrouter

openrouter:
  api_key: ""
  base_url: "https://openrouter.ai/api/v1"
  default_model: "anthropic/claude-3-haiku"

ollama:
  host: "http://localhost:11434"
  model: "llama3"

openai:
  api_key: ""
  base_url: "https://api.openai.com/v1"
  default_model: "gpt-3.5-turbo"

gemini:
  api_key: ""
  default_model: "gemini-pro"

database:
  path: "./mooaid.db"

api:
  host: "0.0.0.0"
  port: 8000

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""
        with open(config_path, "w") as f:
            f.write(default_config)
