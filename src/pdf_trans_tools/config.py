"""
pdf_trans_tools config - Configuration file management
"""
import os
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "pdf_trans_tools.yaml",
    Path.home() / ".config" / "pdf_trans_tools.yml",
    Path.cwd() / ".pdf_trans_tools.yaml",
    Path.cwd() / ".pdf_trans_tools.yml",
]


class Config:
    """Configuration manager for pdf_trans_tools."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config file. If None, searches default locations.
        """
        self._config = {}
        self._loaded_from = None

        if config_path:
            self.load(config_path)
        else:
            self._load_default()

    def _load_default(self) -> None:
        """Load configuration from default locations."""
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                self.load(str(path))
                break

    def load(self, path: str) -> None:
        """
        Load configuration from a YAML file.

        Args:
            path: Path to configuration file

        Raises:
            ImportError: If yaml library is not installed
            FileNotFoundError: If config file does not exist
        """
        if yaml is None:
            raise ImportError("yaml is required for config file support. Install with: pip install pyyaml")

        config_path = Path(path).expanduser().resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with config_path.open("r") as f:
            self._config = yaml.safe_load(f) or {}

        self._loaded_from = str(config_path)

    def get(self, key: str, default=None):
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'api.google_key')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_api_key(self, provider: str = "google") -> Optional[str]:
        """
        Get API key for a provider.

        Args:
            provider: Provider name (default: 'google')

        Returns:
            API key or None
        """
        # Check environment variable first
        env_key = f"{provider.upper()}_API_KEY"
        api_key = os.environ.get(env_key)
        if api_key:
            return api_key

        # Check config file
        return self.get(f"api.{provider}_key")

    def get_target_lang(self) -> str:
        """Get default target language."""
        return self.get("target_lang", "en")

    def get_cache_settings(self) -> dict:
        """Get cache settings."""
        return {
            "enabled": self.get("cache.enabled", True),
            "max_size": self.get("cache.max_size", 1000),
            "ttl": self.get("cache.ttl", 3600),
        }

    @property
    def loaded_from(self) -> Optional[str]:
        """Get the path to the loaded config file."""
        return self._loaded_from


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration.

    Args:
        config_path: Optional path to config file

    Returns:
        Config instance
    """
    return Config(config_path)
