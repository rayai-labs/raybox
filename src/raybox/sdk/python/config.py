"""Configuration management for Raybox SDK."""

import json
from pathlib import Path
from typing import Any


class RayboxConfig:
    """Manages Raybox configuration and credentials."""

    def __init__(self, config_dir: Path | None = None):
        """Initialize config manager.

        Args:
            config_dir: Optional custom config directory. Defaults to ~/.raybox
        """
        self.config_dir = config_dir or Path.home() / ".raybox"
        self.config_file = self.config_dir / "config.json"

    def ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_api_key(self, api_key: str, api_url: str = "https://api.raybox.ai") -> None:
        """Save API key to config file.

        Args:
            api_key: The API key to save
            api_url: The API URL to use (defaults to cloud service)
        """
        self.ensure_config_dir()

        config = {"api_key": api_key, "api_url": api_url}

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

        # Set restrictive permissions (owner read/write only)
        self.config_file.chmod(0o600)

    def load_config(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            dict: Configuration dictionary with api_key and api_url
        """
        if not self.config_file.exists():
            return {}

        with open(self.config_file) as f:
            result: dict[str, Any] = json.load(f)
            return result

    def get_api_key(self) -> str | None:
        """Get stored API key.

        Returns:
            Optional[str]: The API key if found, None otherwise
        """
        config = self.load_config()
        return config.get("api_key")

    def get_api_url(self) -> str:
        """Get stored API URL.

        Returns:
            str: The API URL (defaults to cloud service)
        """
        config = self.load_config()
        url: str = config.get("api_url", "https://api.raybox.ai")
        return url

    def clear(self) -> None:
        """Clear stored configuration."""
        if self.config_file.exists():
            self.config_file.unlink()
